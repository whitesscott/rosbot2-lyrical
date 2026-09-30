#!/usr/bin/env bash
# Start every ROS 2 subsystem needed for a mapping / drive-test session on
# the mini_akm, wait until each is ready, activate slam_toolbox's
# lifecycle, and print connection URLs. Ctrl-C tears everything down
# cleanly.
#
# Usage:
#   ./scripts/drive_test.sh
#
# Env feature flags (all default off unless noted):
#   ENABLE_ROSBRIDGE=1    (default 1)  serve rosbridge on :9090
#                                       for the iPhone Wheeltec app
#   ENABLE_WEB_VIDEO=1    stream /image_raw at :8080 (Foxglove already
#                          covers this, so default off)
#   ENABLE_MEMORY_NODE=1  also run the robot-map VLM captioner
#                          (needs ~/.venvs/robot; adds ~25 s startup)
#
# Assumes bootstrap.sh has been run on the Orin and the wheelbots
# workspace has been colcon-built.

set -uo pipefail

WHEELBOTS="${HOME}/.git/wheelbots"
ROBOTMAP="${HOME}/.git/robot-map"
ROS_DISTRO="${ROS_DISTRO:-kilted}"
LOG_DIR="/tmp/drive_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

ENABLE_ROSBRIDGE="${ENABLE_ROSBRIDGE:-1}"
ENABLE_WEB_VIDEO="${ENABLE_WEB_VIDEO:-0}"
ENABLE_MEMORY_NODE="${ENABLE_MEMORY_NODE:-0}"

# --- source ROS + overlays ------------------------------------------------

set +u
# shellcheck disable=SC1091
source "/opt/ros/${ROS_DISTRO}/setup.bash"
# shellcheck disable=SC1091
[ -f "${WHEELBOTS}/install/setup.bash" ] && source "${WHEELBOTS}/install/setup.bash"
# shellcheck disable=SC1091
[ -f "${ROBOTMAP}/install/setup.bash" ]  && source "${ROBOTMAP}/install/setup.bash"
set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
export PYTHONUNBUFFERED=1

# --- process bookkeeping --------------------------------------------------

PIDS=()

start() {
    local name="$1"; shift
    "$@" > "${LOG_DIR}/${name}.log" 2>&1 &
    local pid=$!
    PIDS+=("${pid}")
    printf "  [%5d] %-12s -> %s/%s.log\n" "${pid}" "${name}" "${LOG_DIR}" "${name}"
}

wait_for_node() {
    local node="$1"
    local timeout_s="${2:-30}"
    local start_ts=$SECONDS
    until ros2 node list 2>/dev/null | grep -q "^${node}$"; do
        if (( SECONDS - start_ts > timeout_s )); then
            echo "  ! timeout waiting for ${node}"
            return 1
        fi
        sleep 1
    done
}

cleanup() {
    echo ""
    echo "[drive_test] shutting down..."
    if (( ${#PIDS[@]} > 0 )); then
        kill "${PIDS[@]}" 2>/dev/null
        sleep 2
        kill -9 "${PIDS[@]}" 2>/dev/null
    fi
    # Belt + suspenders: nuke anything ROS-ish that survived reparenting to init
    pkill -f "wheeltec_robot_node|sllidar_node|v4l2_camera_node|async_slam_toolbox|ekf_node|static_transform_publisher|joint_state_publisher|cmd_vel_to_ackermann|foxglove_bridge|memory_node|rosbridge|web_video_server" 2>/dev/null
    echo "[drive_test] done"
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- launch sequence ------------------------------------------------------

echo "[drive_test] logs -> ${LOG_DIR}"
echo ""
echo "starting subsystems:"

start foxglove   ros2 launch foxglove_bridge foxglove_bridge_launch.xml
sleep 1
start base       ros2 launch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch.py
sleep 3
start lidar      ros2 launch turn_on_wheeltec_robot wheeltec_lidar.launch.py
sleep 2
start camera     ros2 launch turn_on_wheeltec_robot wheeltec_camera_uvc.launch.py
sleep 2

SLAM_CFG="${WHEELBOTS}/install/wheeltec_slam_toolbox/share/wheeltec_slam_toolbox/config/mapper_params_online_async.yaml"
start slam       ros2 run slam_toolbox async_slam_toolbox_node \
    --ros-args --params-file "${SLAM_CFG}" -r odom:=odometry/filtered

if [ "${ENABLE_ROSBRIDGE}" = "1" ]; then
    sleep 2
    start rosbridge ros2 run rosbridge_server rosbridge_websocket
fi

if [ "${ENABLE_WEB_VIDEO}" = "1" ]; then
    sleep 1
    start webvid  ros2 run web_video_server web_video_server
fi

if [ "${ENABLE_MEMORY_NODE}" = "1" ]; then
    sleep 2
    export HF_HOME="${HOME}/.cache/huggingface"
    export HF_HUB_CACHE="${HOME}/.cache/huggingface/hub"
    unset HF_TOKEN
    export PYTHONPATH="${HOME}/.venvs/robot/lib/python3.12/site-packages:${PYTHONPATH:-}"
    start memory  ros2 run robot_memory memory_node
fi

# --- wait for slam then activate ------------------------------------------

echo ""
echo "[drive_test] waiting for /slam_toolbox to register..."
if wait_for_node "/slam_toolbox" 30; then
    ros2 lifecycle set /slam_toolbox configure > /dev/null && \
    ros2 lifecycle set /slam_toolbox activate  > /dev/null && \
        echo "[drive_test] slam_toolbox active"
fi

# --- print connection info ------------------------------------------------

IP=$(ip -brief addr show | awk '$2=="UP" && $3 ~ /^192\./ {split($3,a,"/"); print a[1]; exit}')
IP="${IP:-<orin-ip>}"

cat <<EOF

=== drive_test ready ===

  Foxglove Studio:    ws://${IP}:8765
EOF
[ "${ENABLE_ROSBRIDGE}"  = "1" ] && echo "  iPhone Wheeltec:   ws://${IP}:9090   (or point the app at ${IP})"
[ "${ENABLE_WEB_VIDEO}"  = "1" ] && echo "  Web video:         http://${IP}:8080/stream_viewer?topic=/image_raw"
[ "${ENABLE_MEMORY_NODE}" = "1" ] && echo "  memory_node:       tail ${LOG_DIR}/memory.log for captions as you drive"

cat <<EOF

  logs:              ${LOG_DIR}/
  save map when done: ros2 run nav2_map_server map_saver_cli -f ~/house_map

Ctrl-C to shut down cleanly.

EOF

# --- block until Ctrl-C ---------------------------------------------------

wait
