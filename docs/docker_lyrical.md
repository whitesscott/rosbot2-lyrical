# Lyrical container (Isaac ROS + ZED)

On the `lyrical` branch the stack runs inside a container instead of on the host. The image is a thin layer over the Isaac ROS + ZED image built by `isaac-ros-cli` (`isaac_ros_dev-zed:latest`: ROS 2 Lyrical, CUDA, ZED SDK, `zed-ros2-wrapper`), so the robot base, lidar, SLAM, Nav2, the ZED wrapper and the `robot_memory` VLM node all share one ROS graph and one GPU runtime.

## One-time setup

Host prerequisites (unchanged from `kilted`, see [`bootstrap.md`](bootstrap.md)): the udev rules that create `/dev/wheeltec_controller` and `/dev/wheeltec_laser`, and the `isaac_ros_dev-zed:latest` image.

```sh
./scripts/docker_run.sh image    # build wheelbots:lyrical (apt deps only)
./scripts/docker_run.sh build    # colcon build --symlink-install in the container
```

`image` passes `--builder default` on purpose: a docker-container buildx builder cannot see the local base image.

## Daily use

```sh
./scripts/docker_run.sh                                                   # shell (a second call joins the running container)
./scripts/docker_run.sh /opt/wheelbots_ws/src/wheelbots/scripts/drive_test.sh
ENABLE_MEMORY_NODE=1 ./scripts/docker_run.sh /opt/wheelbots_ws/src/wheelbots/scripts/drive_test.sh
./scripts/docker_run.sh ros2 launch wheeltec_nav2 wheeltec_nav2.launch.py
```

The container is `--rm`: it goes away when its first command exits. Everything that must persist is mounted:

| In the container | On the host | Notes |
|---|---|---|
| `/opt/wheelbots_ws/src/wheelbots` | this repo | edits are live (`--symlink-install`) |
| `/opt/wheelbots_ws/{build,install,log}` | docker volume `wheelbots_lyrical_ws` | kept apart from a host-side Kilted build in the repo; `docker volume rm wheelbots_lyrical_ws` for a clean rebuild |
| `/opt/robot-venv` (read-only) | `~/.venvs/robot` | torch + transformers for `robot_memory` |
| `/root/.cache/huggingface` | `~/.cache/huggingface` | model weights |
| `/root/.local/share/robot-map` | `~/.local/share/robot-map` | keyframe thumbnails + Chroma DB |
| `/usr/local/zed/{settings,resources}` | `~/.zed/{settings,resources}` | calibration, optimized depth models |
| `/workspaces/isaac_ros-dev` | `~/workspaces/isaac_ros-dev` | `scripts/zed-up.sh`, Isaac ROS sources |

The container runs as root, so files it creates in those host directories are root-owned. To use them from the host again: `sudo chown -R $USER ~/.local/share/robot-map`.

## AI: `robot_memory`

`ai/robot_memory` is the spatial-memory package (previously the separate `robot-map` repo): keyframes are captioned by Qwen3-VL-2B on the GPU, embedded, and stored in Chroma with the robot pose. torch is not in the image; `drive_test.sh` puts the mounted host venv (`ROBOT_VENV_SITE`) on `PYTHONPATH` for the `memory_node` process only, so it cannot shadow the numpy that the `ros2` CLI needs.

```sh
# standalone, in a container shell
PYTHONPATH="$ROBOT_VENV_SITE:$PYTHONPATH" ros2 run robot_memory memory_node
PYTHONPATH="$ROBOT_VENV_SITE:$PYTHONPATH" python3 -m robot_memory.query "where is the fireplace?"
```

## LLM access: `ros-mcp`

[`ros-mcp`](https://pypi.org/project/ros-mcp/) is an MCP server that lets an LLM client (Claude Code, Claude Desktop, ...) inspect and command the robot through rosbridge. It runs on the host, not in the container, and only needs the rosbridge + rosapi pair that `drive_test.sh` starts by default on `:9090`.

```sh
uv pip install --python ~/.venvs/robot/bin/python ros-mcp
claude mcp add -s user ros-mcp -e ROSBRIDGE_IP=127.0.0.1 -e ROSBRIDGE_PORT=9090 \
    -- ~/.venvs/robot/bin/ros-mcp --transport=stdio
```

It exposes read tools (`get_topics`, `get_nodes`, `subscribe_once`, ...) and write tools (`publish_once`, `publish_for_durations`, `call_service`, `send_action_goal`, `set_parameter`). The write tools can drive the robot: test them with the wheels off the ground. rosbridge itself is unauthenticated and reachable from the LAN.

## ZED Mini

The wrapper is already in the image. Once the camera is connected, skip the UVC camera and point the memory node at the ZED image (`bgra8` is decoded natively):

```sh
./scripts/docker_run.sh /workspaces/isaac_ros-dev/scripts/zed-up.sh        # terminal 1
ENABLE_CAMERA=0 ENABLE_MEMORY_NODE=1 IMAGE_TOPIC=/zed/zed_node/rgb/color/rect/image \
    ./scripts/docker_run.sh /opt/wheelbots_ws/src/wheelbots/scripts/drive_test.sh   # terminal 2
```

Still to do when it arrives: replace the `base_to_camera` static transform in `robot_mode_description.launch.py` with the measured ZED mount pose (and let the wrapper publish the camera's own frames), check the topic name above against `ros2 topic list`, and feed ZED depth into the Nav2 costmaps or nvblox (`ros-lyrical-isaac-ros-nvblox` is available from apt).

## What changed for Lyrical

- `tf2`, `tf2_ros` and `message_filters` `.h` headers are gone: includes switched to `.hpp`; `message_filters::Subscriber` takes an `rclcpp::QoS`.
- `static_transform_publisher` no longer accepts positional arguments (`--x … --frame-id … --child-frame-id …`), and `robot_state_publisher` takes the URDF as the `robot_description` parameter rather than a file argument.
- Nav2 1.5: `param_mini_akm.yaml` ported (`::` plugin names, `behavior_server` instead of `recoveries_server`, built-in BT node list, `max_linear_vel`), and it is now the default parameter file. **The other `param_*.yaml` files are still Humble-era and will not bring Nav2 up as-is.**
- `drive_test.sh` retries the slam_toolbox lifecycle transitions and resolves paths from its own location and `ros2 pkg prefix`.

## Not available on Lyrical (noble)

- `ros-lyrical-pcl-ros` / `pcl-conversions` (need libpcl 1.15) — only the ignored `lslidar_driver` used them.
- `cartographer_ros`, `rtabmap_ros` — the `wheeltec_cartographer` and `wheeltec_robot_rtab` launch files build but cannot run.
- `isaac_ros_visual_slam` has no apt package; build it from `~/workspaces/isaac_ros-dev/src` if wanted.
