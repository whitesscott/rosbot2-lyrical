#!/usr/bin/env bash
# Start the rosbot2 Lyrical container (Isaac ROS + ZED + wheelbots), or open
# another shell in it if it is already running.
#
# Usage:
#   ./scripts/docker_run.sh image            build the rosbot2:lyrical image
#   ./scripts/docker_run.sh                  interactive shell
#   ./scripts/docker_run.sh <command...>     run a command with ROS sourced, e.g.
#       ./scripts/docker_run.sh /opt/wheelbots_ws/src/wheelbots/scripts/drive_test.sh
#   ./scripts/docker_run.sh --dev [command...]
#                                            same, with this checkout mounted
#                                            over the sources baked into the image
#   ./scripts/docker_run.sh build [args...]  colcon build the mounted checkout
#                                            (implies --dev)
#
# By default the container runs the workspace that was built into the image.
# With --dev, this checkout is bind-mounted at /opt/wheelbots_ws/src/wheelbots
# and build/install/log live in a named volume, so edits are live and a
# rebuild survives the container. Without --dev, changes need a new image.
#
# Layout inside the container:
#   /opt/wheelbots_ws                 colcon workspace (image, or volume with --dev)
#   /opt/wheelbots_ws/src/wheelbots   this repo (image copy, or bind mount with --dev)
#   /opt/ros_ws                       zed-ros2-wrapper workspace (from the image)
#   /opt/robot-venv                   venv with torch/transformers for
#                                     robot_memory (from the image, or a host
#                                     venv when ROBOT_VENV is set)
#
# Environment:
#   WHEELBOTS_IMAGE   image tag (default: rosbot2:lyrical)
#   WHEELBOTS_DEV     1 = same as --dev
#   ROS_DOMAIN_ID     DDS domain (default: 10). Machines that should see each
#                     other's topics (Orin, Thor) must use the same value.
#   RMW_IMPLEMENTATION  middleware (default: rmw_fastrtps_cpp, the only one in
#                     the image). Must also match across machines.
#   ROBOT_VENV        host venv to mount over the image's /opt/robot-venv
#                     (default: unset, use the venv in the image)
#   ISAAC_ROS_WS      Isaac ROS workspace to mount (default: ~/workspaces/isaac_ros-dev)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${WHEELBOTS_IMAGE:-rosbot2:lyrical}"
DEV="${WHEELBOTS_DEV:-0}"
NAME="wheelbots-lyrical"
WS_VOLUME="wheelbots_lyrical_ws"
ROBOT_VENV="${ROBOT_VENV:-}"
ISAAC_WS="${ISAAC_ROS_WS:-$HOME/workspaces/isaac_ros-dev}"
ZED_SETTINGS="$HOME/.zed/settings"
ZED_RESOURCES="$HOME/.zed/resources"

if [ "${1:-}" = "image" ]; then
  # The default builder writes straight into the local image store; a
  # docker-container builder would have to export and re-load ~35 GB.
  exec docker buildx build --builder default --load \
    -f "$REPO_DIR/docker/Dockerfile.rosbot2" -t "$IMAGE" "$REPO_DIR"
fi

if [ "${1:-}" = "--dev" ]; then
  DEV=1
  shift
fi

if ! docker image inspect "$IMAGE" > /dev/null 2>&1; then
  echo "ERROR: image $IMAGE not found; build it with: $0 image" >&2
  exit 1
fi

# Run commands through an interactive bash so /etc/bash.bashrc sources ROS,
# the ZED wrapper workspace and the wheelbots overlay.
if [ "$#" -eq 0 ]; then
  set -- bash
elif [ "$1" = "build" ]; then
  DEV=1
  shift
  set -- bash -ic 'cd "$WHEELBOTS_WS" && exec colcon build --symlink-install "$@"' bash "$@"
else
  set -- bash -ic 'exec "$@"' bash "$@"
fi

TTY_ARGS=(-i)
[ -t 0 ] && TTY_ARGS+=(-t)

# A second terminal joins the running container instead of failing on the name.
if [ -n "$(docker ps -q -f "name=^${NAME}$")" ]; then
  exec docker exec "${TTY_ARGS[@]}" "$NAME" "$@"
fi

# X11: pass the X authority file so root in the container can open windows.
X11_ARGS=()
if [ -n "${DISPLAY:-}" ]; then
  XAUTH_FILE="${XAUTHORITY:-$HOME/.Xauthority}"
  if [ -f "$XAUTH_FILE" ]; then
    X11_ARGS+=(-v "$XAUTH_FILE":/root/.Xauthority:ro -e XAUTHORITY=/root/.Xauthority)
  fi
  case "$DISPLAY" in
    :*) xhost +si:localuser:root > /dev/null 2>&1 || true ;;
  esac
else
  echo "note: DISPLAY is not set, so GUI tools (rviz2, rqt) will not open." >&2
  echo "      Connect with 'ssh -X', or run from a terminal in the desktop session." >&2
fi

# --dev: this checkout over the baked sources, build tree in a named volume.
DEV_ARGS=()
if [ "$DEV" = "1" ]; then
  DEV_ARGS=(-v "$WS_VOLUME":/opt/wheelbots_ws -v "$REPO_DIR":/opt/wheelbots_ws/src/wheelbots)
fi

OPT_ARGS=()

# robot_memory: optional host venv override, model cache, and the keyframe store.
if [ -n "$ROBOT_VENV" ]; then
  if [ -d "$ROBOT_VENV/lib/python3.12/site-packages" ]; then
    OPT_ARGS+=(-v "$ROBOT_VENV":/opt/robot-venv:ro)
  else
    echo "note: ROBOT_VENV=$ROBOT_VENV has no python3.12 site-packages; using the image's venv." >&2
  fi
fi
mkdir -p "$HOME/.cache/huggingface" "$HOME/.local/share/robot-map"
OPT_ARGS+=(-v "$HOME/.cache/huggingface":/root/.cache/huggingface)
OPT_ARGS+=(-v "$HOME/.local/share/robot-map":/root/.local/share/robot-map)

# rviz2 keeps its layout and persistent settings in ~/.rviz2; without this it
# reports "Could not open file: /root/.rviz2/persistent_settings" on every
# start and forgets the layout when the container exits.
mkdir -p "$HOME/.rviz2"
OPT_ARGS+=(-v "$HOME/.rviz2":/root/.rviz2)

# ZED: calibration and optimized neural depth models survive the container.
mkdir -p "$ZED_SETTINGS"
OPT_ARGS+=(-v "$ZED_SETTINGS":/usr/local/zed/settings)
if [ -d "$ZED_RESOURCES" ] && [ -n "$(ls -A "$ZED_RESOURCES")" ]; then
  OPT_ARGS+=(-v "$ZED_RESOURCES":/usr/local/zed/resources)
fi

# jtop: the service runs on the host; the client in the image talks to its
# socket. Only mounted when it exists: docker would otherwise create a
# directory at that path on the host.
# The socket is group-owned by the host's 'jtop' group, whose GID differs per
# machine (it is whatever was free when jtop was installed), so it is looked
# up here and added by number. START_SETUP then gives that GID a name inside
# the container, which keeps 'groups' in /etc/bash.bashrc from warning that
# it cannot find a name for the group ID.
if [ -S /run/jtop.sock ]; then
  OPT_ARGS+=(-v /run/jtop.sock:/run/jtop.sock)
  JTOP_GID="$(getent group jtop | cut -d: -f3 || true)"
  if [ -n "$JTOP_GID" ]; then
    OPT_ARGS+=(--group-add "$JTOP_GID" -e JTOP_GID="$JTOP_GID")
  fi
fi

# Runs once, as root, before the command when the container is created.
START_SETUP='# Qt wants a private runtime directory; without one it warns on every start.
mkdir -p "$XDG_RUNTIME_DIR" && chmod 700 "$XDG_RUNTIME_DIR"
if [ -n "${JTOP_GID:-}" ] && ! getent group "$JTOP_GID" > /dev/null; then
  groupadd -g "$JTOP_GID" jtop 2> /dev/null || true
fi
exec "$@"'

# Isaac ROS workspace (zed-up.sh, zed-overrides.yaml, visual_slam / nvblox sources).
if [ -d "$ISAAC_WS" ]; then
  OPT_ARGS+=(-v "$ISAAC_WS":/workspaces/isaac_ros-dev)
fi

exec docker run "${TTY_ARGS[@]}" --rm --name "$NAME" \
  --runtime=nvidia --gpus=all --privileged \
  --network host --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix "${X11_ARGS[@]}" \
  -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-10}" \
  -e RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}" \
  -e ROS_AUTOMATIC_DISCOVERY_RANGE -e ROS_STATIC_PEERS \
  -e XDG_RUNTIME_DIR=/tmp/runtime-root \
  -e ENABLE_ROSBRIDGE -e ENABLE_WEB_VIDEO -e ENABLE_MEMORY_NODE -e ENABLE_CAMERA -e IMAGE_TOPIC \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v /dev:/dev \
  "${DEV_ARGS[@]}" \
  "${OPT_ARGS[@]}" \
  "$IMAGE" bash -c "$START_SETUP" bash "$@"
