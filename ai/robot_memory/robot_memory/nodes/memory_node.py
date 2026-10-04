"""ROS 2 node that turns keyframes into captioned, embedded memories.

Subscribes to an image topic and the TF tree. Whenever the robot has
moved farther than `keyframe_distance_m` OR turned more than
`keyframe_yaw_deg` since the last accepted keyframe, it grabs the
current image, extracts the current pose (map -> base_footprint by
default, or fall back to odom -> base_footprint), and hands the tuple
off to a background worker. The worker captions with Qwen3-VL-2B,
embeds the caption with BGE-small, saves a JPEG thumbnail, and
persists everything to Chroma.

The worker queue is bounded — when captioning falls behind travel the
oldest queued frame is dropped rather than backing up. This keeps
memory bounded and the callback fast.

Parameters:

    image_topic (string, default "/image_raw")
    map_frame (string, default "map")
    fallback_frame (string, default "odom")
    base_frame (string, default "base_footprint")
    keyframe_distance_m (double, default 1.0)
    keyframe_yaw_deg (double, default 30.0)
    thumbnails_dir (string, default ~/.local/share/robot-map/keyframes)
    db_path (string, default ~/.local/share/robot-map/chroma_db)
    worker_queue_size (int, default 4)
    caption_max_tokens (int, default 80)
"""

from __future__ import annotations

import math
import os
import queue
import threading
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import rclpy
from geometry_msgs.msg import Quaternion, TransformStamped
from PIL import Image as PILImage
from rclpy.node import Node
from sensor_msgs.msg import Image
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener


def yaw_from_quaternion(q: Quaternion) -> float:
    """Extract yaw (Z rotation) from a geometry_msgs Quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def wrap_pi(a: float) -> float:
    """Wrap angle to (-pi, pi]."""
    return (a + math.pi) % (2.0 * math.pi) - math.pi


class MemoryNode(Node):
    def __init__(self) -> None:
        super().__init__("memory_node")

        self.declare_parameter("image_topic", "/image_raw")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("fallback_frame", "odom")
        self.declare_parameter("base_frame", "base_footprint")
        self.declare_parameter("keyframe_distance_m", 1.0)
        self.declare_parameter("keyframe_yaw_deg", 30.0)
        self.declare_parameter(
            "thumbnails_dir",
            str(Path.home() / ".local" / "share" / "robot-map" / "keyframes"),
        )
        self.declare_parameter(
            "db_path",
            str(Path.home() / ".local" / "share" / "robot-map" / "chroma_db"),
        )
        self.declare_parameter("worker_queue_size", 4)
        self.declare_parameter("caption_max_tokens", 80)

        self.image_topic = self.get_parameter("image_topic").value
        self.map_frame = self.get_parameter("map_frame").value
        self.fallback_frame = self.get_parameter("fallback_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        self.keyframe_distance_m = float(self.get_parameter("keyframe_distance_m").value)
        self.keyframe_yaw_rad = math.radians(float(self.get_parameter("keyframe_yaw_deg").value))
        self.thumbnails_dir = Path(self.get_parameter("thumbnails_dir").value)
        self.db_path = Path(self.get_parameter("db_path").value)
        qsize = int(self.get_parameter("worker_queue_size").value)
        self.caption_max_tokens = int(self.get_parameter("caption_max_tokens").value)

        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

        # TF listener for pose lookup.
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # NOTE: cv_bridge is deliberately NOT used. On this Kilted install
        # cv_bridge's boost extension is compiled against numpy 1.x, which
        # collides with the rest of the venv (scipy/sklearn need numpy>=2).
        # For our rgb8 / bgr8 stream the conversion is a two-liner via numpy
        # frombuffer, so we skip the dependency.

        # Keyframe gate state.
        self.last_kf_xy: Optional[Tuple[float, float]] = None
        self.last_kf_yaw: Optional[float] = None
        self.pending_count = 0
        self.stored_count = 0
        self.dropped_count = 0

        # Bounded worker queue. Elements are
        # (PIL.Image, (x, y), yaw, header_stamp_seconds).
        self.work_queue: "queue.Queue" = queue.Queue(maxsize=qsize)
        self._stop = threading.Event()
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

        # Subscribe last so callbacks don't fire before state is ready.
        self.sub = self.create_subscription(
            Image, self.image_topic, self._image_cb, 10
        )

        self.get_logger().info(
            f"memory_node up: image_topic={self.image_topic!r} "
            f"kf_gate=({self.keyframe_distance_m:.2f} m OR "
            f"{math.degrees(self.keyframe_yaw_rad):.0f} deg) "
            f"queue={qsize} thumbnails={self.thumbnails_dir}"
        )

    # --- pose lookup --------------------------------------------------------

    def _lookup_pose(self, stamp) -> Optional[Tuple[float, float, float, str]]:
        """Return (x, y, yaw, frame_used) or None if TF is unavailable."""
        for frame in (self.map_frame, self.fallback_frame):
            try:
                t: TransformStamped = self.tf_buffer.lookup_transform(
                    frame, self.base_frame, rclpy.time.Time()
                )
            except Exception:
                continue
            x = t.transform.translation.x
            y = t.transform.translation.y
            yaw = yaw_from_quaternion(t.transform.rotation)
            return x, y, yaw, frame
        return None

    # --- keyframe gate ------------------------------------------------------

    def _accept_keyframe(self, x: float, y: float, yaw: float) -> bool:
        if self.last_kf_xy is None:
            return True
        dx = x - self.last_kf_xy[0]
        dy = y - self.last_kf_xy[1]
        if (dx * dx + dy * dy) ** 0.5 >= self.keyframe_distance_m:
            return True
        if abs(wrap_pi(yaw - self.last_kf_yaw)) >= self.keyframe_yaw_rad:
            return True
        return False

    # --- image callback -----------------------------------------------------

    def _image_cb(self, msg: Image) -> None:
        pose = self._lookup_pose(msg.header.stamp)
        if pose is None:
            # TF not ready yet; skip silently.
            return
        x, y, yaw, _frame = pose

        if not self._accept_keyframe(x, y, yaw):
            return

        pil_img = self._image_msg_to_pil(msg)
        if pil_img is None:
            return

        stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        try:
            self.work_queue.put_nowait((pil_img, (x, y), yaw, stamp_sec))
        except queue.Full:
            self.dropped_count += 1
            self.get_logger().warn(
                f"work queue full, dropping keyframe (total dropped: {self.dropped_count})"
            )
            return

        self.last_kf_xy = (x, y)
        self.last_kf_yaw = yaw
        self.pending_count += 1

    # --- worker thread ------------------------------------------------------

    def _worker_loop(self) -> None:
        # Lazy-load models inside the worker so the main ROS thread doesn't
        # block on the ~20 s cold model load. Callbacks that fire before the
        # models are up will drop cleanly via the bounded queue.
        from robot_memory.captioner import Captioner
        from robot_memory.embedder import Embedder
        from robot_memory.store import Keyframe, Store

        self.get_logger().info("worker: loading models...")
        captioner = Captioner(max_new_tokens=self.caption_max_tokens)
        embedder = Embedder()
        store = Store(db_path=self.db_path)
        # Force load so first inference is warm.
        captioner._ensure_loaded()
        embedder._ensure_loaded()
        self.get_logger().info(
            f"worker: ready (embedding_dim={embedder.dim}, "
            f"existing_keyframes={store.count()})"
        )

        while not self._stop.is_set():
            try:
                pil_img, xy, yaw, stamp_sec = self.work_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                caption = captioner.caption(pil_img)
                vec = embedder.encode(caption)[0]
                kf = Keyframe(
                    caption=caption,
                    embedding=vec,
                    pose_xy=xy,
                    pose_yaw=yaw,
                    timestamp=stamp_sec,
                )
                # Save a small thumbnail keyed by the assigned id.
                thumb_path = self.thumbnails_dir / f"{kf.keyframe_id}.jpg"
                self._save_thumbnail(pil_img, thumb_path)
                kf.thumbnail_path = str(thumb_path)
                store.add(kf)
                self.stored_count += 1
                self.get_logger().info(
                    f"[{self.stored_count:04d}] xy=({xy[0]:+.2f},{xy[1]:+.2f}) "
                    f"yaw={math.degrees(yaw):+.0f}  {caption[:80]}"
                )
            except Exception as e:  # noqa: BLE001
                self.get_logger().error(f"worker: caption/store failed: {e}")
            finally:
                self.pending_count = max(0, self.pending_count - 1)
                self.work_queue.task_done()

    @staticmethod
    def _save_thumbnail(pil_img: PILImage.Image, path: Path) -> None:
        # Thumbnails at 480 px longest side keep the store folder small and
        # still show enough detail for a human to recognise the scene.
        thumb = pil_img.copy()
        thumb.thumbnail((480, 480))
        thumb.save(path, format="JPEG", quality=80)

    def _image_msg_to_pil(self, msg: Image):
        """Decode a sensor_msgs/Image into a PIL Image without cv_bridge.

        Supports rgb8 / bgr8 (v4l2 UVC camera) and rgba8 / bgra8 (the ZED
        wrapper publishes bgra8). Any other encoding is logged and dropped.
        """
        enc = msg.encoding
        channels = {"rgb8": 3, "bgr8": 3, "rgba8": 4, "bgra8": 4}.get(enc)
        if channels is None:
            self.get_logger().warn(
                f"unsupported image encoding {enc!r}; expected rgb8/bgr8/rgba8/bgra8"
            )
            return None
        try:
            arr = np.frombuffer(msg.data, dtype=np.uint8)
            arr = arr.reshape(msg.height, msg.step)[:, : msg.width * channels]
            arr = arr.reshape(msg.height, msg.width, channels)[:, :, :3]
        except Exception as e:  # noqa: BLE001
            self.get_logger().warn(f"image reshape failed: {e}")
            return None
        if enc.startswith("bgr"):
            arr = arr[:, :, ::-1]
        return PILImage.fromarray(np.ascontiguousarray(arr), mode="RGB")

    # --- shutdown -----------------------------------------------------------

    def destroy_node(self) -> None:
        self._stop.set()
        self.worker.join(timeout=2.0)
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MemoryNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
