#!/usr/bin/env bash
# Start the wheelbots Lyrical container (Isaac ROS + ZED base), or open
# another shell in it if it is already running.
#
# Usage:
#   ./scripts/docker_run.sh                  interactive shell
#   ./scripts/docker_run.sh build [args...]  colcon build the workspace
#   ./scripts/docker_run.sh image            (re)build the wheelbots:lyrical image
#   ./scripts/docker_run.sh <command...>     run a command with ROS sourced, e.g.
#       ./scripts/docker_run.sh /opt/wheelbots_ws/src/wheelbots/scripts/drive_test.sh
#
# Layout inside the container:
#   /opt/wheelbots_ws                 colcon workspace (named volume, so the
#                                     Lyrical build/install/log never touch a
#                                     host-side Kilted build in the repo)
#   /opt/wheelbots_ws/src/wheelbots   this repo (bind mount)
#   /opt/ros_ws                       zed-ros2-wrapper workspace (from the image)
#   /opt/robot-venv                   host uv venv with torch/transformers for
#                                     robot_memory (read-only, if present)
#
# Environment:
#   WHEELBOTS_IMAGE   image tag (default: wheelbots:lyrical)
#   ROBOT_VENV        host venv for robot_memory (default: ~/.venvs/robot)
#   ISAAC_ROS_WS      Isaac ROS workspace to mount (default: ~/workspaces/isaac_ros-dev)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${WHEELBOTS_IMAGE:-wheelbots:lyrical}"
NAME="wheelbots-lyrical"
WS_VOLUME="wheelbots_lyrical_ws"
ROBOT_VENV="${ROBOT_VENV:-$HOME/.venvs/robot}"
ISAAC_WS="${ISAAC_ROS_WS:-$HOME/workspaces/isaac_ros-dev}"
ZED_SETTINGS="$HOME/.zed/settings"
ZED_RESOURCES="$HOME/.zed/resources"

if [ "${1:-}" = "image" ]; then
  # The default builder is named explicitly: a docker-container builder (such
  # as a selected buildx 'cuda' builder) cannot see the local base image.
  exec docker buildx build --builder default --load \
    -f "$REPO_DIR/docker/Dockerfile.lyrical" -t "$IMAGE" "$REPO_DIR/docker"
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
fi

OPT_ARGS=()

# robot_memory: torch/transformers venv, model cache, and the keyframe store.
if [ -d "$ROBOT_VENV/lib/python3.12/site-packages" ]; then
  OPT_ARGS+=(-v "$ROBOT_VENV":/opt/robot-venv:ro)
else
  echo "note: $ROBOT_VENV not found; memory_node will be unavailable." >&2
fi
mkdir -p "$HOME/.cache/huggingface" "$HOME/.local/share/robot-map"
OPT_ARGS+=(-v "$HOME/.cache/huggingface":/root/.cache/huggingface)
OPT_ARGS+=(-v "$HOME/.local/share/robot-map":/root/.local/share/robot-map)

# ZED: calibration and optimized neural depth models survive the container.
mkdir -p "$ZED_SETTINGS"
OPT_ARGS+=(-v "$ZED_SETTINGS":/usr/local/zed/settings)
if [ -d "$ZED_RESOURCES" ] && [ -n "$(ls -A "$ZED_RESOURCES")" ]; then
  OPT_ARGS+=(-v "$ZED_RESOURCES":/usr/local/zed/resources)
fi

# Isaac ROS workspace (zed-up.sh, zed-overrides.yaml, visual_slam / nvblox sources).
if [ -d "$ISAAC_WS" ]; then
  OPT_ARGS+=(-v "$ISAAC_WS":/workspaces/isaac_ros-dev)
fi

exec docker run "${TTY_ARGS[@]}" --rm --name "$NAME" \
  --runtime=nvidia --gpus=all --privileged \
  --network host --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix "${X11_ARGS[@]}" \
  -e ROS_DOMAIN_ID -e ROS_AUTOMATIC_DISCOVERY_RANGE -e ROS_STATIC_PEERS -e RMW_IMPLEMENTATION \
  -e ENABLE_ROSBRIDGE -e ENABLE_WEB_VIDEO -e ENABLE_MEMORY_NODE -e ENABLE_CAMERA -e IMAGE_TOPIC \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v /dev:/dev \
  -v "$WS_VOLUME":/opt/wheelbots_ws \
  -v "$REPO_DIR":/opt/wheelbots_ws/src/wheelbots \
  "${OPT_ARGS[@]}" \
  "$IMAGE" "$@"
