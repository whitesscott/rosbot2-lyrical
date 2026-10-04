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
#   ENABLE_ROSBRIDGE=1    (default 1)  serve rosbridge + rosapi on :9090
#                                       for the iPhone Wheeltec app and
#                                       MCP clients (ros-mcp)
#   ENABLE_WEB_VIDEO=1    stream /image_raw at :8080 (Foxglove already
#                          covers this, so default off)
#   ENABLE_MEMORY_NODE=1  also run the robot_memory VLM captioner
#                          (ai/robot_memory; needs the torch venv, see
#                          ROBOT_VENV_SITE; adds ~25 s startup)
#   ENABLE_CAMERA=0       (default 1)  skip the v4l2 UVC camera, e.g. when
#                          the ZED wrapper publishes images instead
#   IMAGE_TOPIC=<topic>   image topic for memory_node (default /image_raw)
#
# Runs either on the host (after bootstrap.sh + colcon build) or inside the
# Lyrical container (scripts/docker_run.sh), where the image presets
# ROS_DISTRO, WHEELBOTS_INSTALL and ROBOT_VENV_SITE.

set -uo pipefail

WHEELBOTS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHEELBOTS_INSTALL="${WHEELBOTS_INSTALL:-${WHEELBOTS}/install}"
ROS_DISTRO="${ROS_DISTRO:-lyrical}"
ROBOT_VENV_SITE="${ROBOT_VENV_SITE:-${HOME}/.venvs/robot/lib/python3.12/site-packages}"
LOG_DIR="/tmp/drive_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

ENABLE_ROSBRIDGE="${ENABLE_ROSBRIDGE:-1}"
ENABLE_WEB_VIDEO="${ENABLE_WEB_VIDEO:-0}"
ENABLE_MEMORY_NODE="${ENABLE_MEMORY_NODE:-0}"
ENABLE_CAMERA="${ENABLE_CAMERA:-1}"
IMAGE_TOPIC="${IMAGE_TOPIC:-/image_raw}"

# --- source ROS + overlays ------------------------------------------------

set +u
# shellcheck disable=SC1091
source "/opt/ros/${ROS_DISTRO}/setup.bash"
# shellcheck disable=SC1091
[ -f "${WHEELBOTS_INSTALL}/setup.bash" ] && source "${WHEELBOTS_INSTALL}/setup.bash"
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
    # Disarm the trap so a normal exit or a second Ctrl-C doesn't re-enter.
    trap - INT TERM EXIT
    echo ""
    echo "[drive_test] shutting down..."
    if (( ${#PIDS[@]} > 0 )); then
        kill "${PIDS[@]}" 2>/dev/null
        sleep 2
        kill -9 "${PIDS[@]}" 2>/dev/null
    fi
    # Belt + suspenders: ros2 launch's children reparent to init on signal,
    # so kill the specific reparented nodes. Anchor patterns to install-path
    # fragments so we can't accidentally match an unrelated user process
    # (e.g. `less some_rosbridge.log`).
    pkill -x static_transform_publisher 2>/dev/null
    pkill -x rosbridge_websocket 2>/dev/null
    pkill -x rosapi_node 2>/dev/null
    pkill -x web_video_server 2>/dev/null
    pkill -f 'install/[^/]*/lib/[^/]*/(wheeltec_robot_node|sllidar_node|v4l2_camera_node|async_slam_toolbox_node|memory_node|foxglove_bridge)$' 2>/dev/null
    pkill -f 'install/turn_on_wheeltec_robot/lib/turn_on_wheeltec_robot/cmd_vel_to_ackermann_drive\.py$' 2>/dev/null
    pkill -f 'robot_localization/ekf_node' 2>/dev/null
    pkill -f 'joint_state_publisher/joint_state_publisher' 2>/dev/null
    echo "[drive_test] done"
}
# EXIT fires on any exit path (Ctrl-C, SIGTERM, or `wait` returning because
# every launch crashed) — earlier this trap only handled signals, so a
# natural exit path left orphaned nodes running.
trap cleanup INT TERM EXIT

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
if [ "${ENABLE_CAMERA}" = "1" ]; then
    start camera ros2 launch turn_on_wheeltec_robot wheeltec_camera_uvc.launch.py
    sleep 2
fi

SLAM_CFG="$(ros2 pkg prefix wheeltec_slam_toolbox 2>/dev/null)/share/wheeltec_slam_toolbox/config/mapper_params_online_async.yaml"
# Guard: without the install-space params file, slam_toolbox exits silently
# and the operator drives thinking mapping is happening.
if [ ! -f "$SLAM_CFG" ]; then
    echo "[drive_test] !! SLAM params file missing:"
    echo "                ${SLAM_CFG}"
    echo "                did you 'colcon build' the workspace yet?"
    exit 1
fi
start slam       ros2 run slam_toolbox async_slam_toolbox_node \
    --ros-args --params-file "${SLAM_CFG}" -r odom:=odometry/filtered

if [ "${ENABLE_ROSBRIDGE}" = "1" ]; then
    sleep 2
    start rosbridge ros2 run rosbridge_server rosbridge_websocket
    # rosapi answers the /rosapi/* introspection services (topic, service,
    # node and parameter listings) that MCP clients such as ros-mcp rely on.
    start rosapi    ros2 run rosapi rosapi_node
fi

if [ "${ENABLE_WEB_VIDEO}" = "1" ]; then
    sleep 1
    start webvid  ros2 run web_video_server web_video_server
fi

if [ "${ENABLE_MEMORY_NODE}" = "1" ]; then
    sleep 2
    # Scope env vars to just the memory_node process via `env` — earlier we
    # exported PYTHONPATH into the parent shell, and the venv's numpy/urllib3
    # then infected the subsequent `ros2` CLI calls (lifecycle set,
    # node list), silently breaking slam_toolbox activation.
    VENV_SITE="${ROBOT_VENV_SITE}"
    if [ ! -d "$VENV_SITE" ]; then
        echo "  ! memory_node skipped: $VENV_SITE not found (rebuild venv?)"
    else
        start memory env -u HF_TOKEN \
            HF_HOME="${HOME}/.cache/huggingface" \
            HF_HUB_CACHE="${HOME}/.cache/huggingface/hub" \
            PYTHONPATH="${VENV_SITE}${PYTHONPATH:+:${PYTHONPATH}}" \
            ros2 run robot_memory memory_node \
            --ros-args -p image_topic:="${IMAGE_TOPIC}"
    fi
fi

# --- wait for slam then activate ------------------------------------------

echo ""
echo "[drive_test] waiting for /slam_toolbox to register..."
if wait_for_node "/slam_toolbox" 30; then
    # The node shows up in `ros2 node list` before its lifecycle services
    # are discoverable, so a transition requested right away can fail.
    # Retry until the node reports active.
    slam_state=""
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        slam_state="$(ros2 lifecycle get /slam_toolbox 2>/dev/null | awk '{print $1}')"
        case "${slam_state}" in
            active)       break ;;
            unconfigured) ros2 lifecycle set /slam_toolbox configure > /dev/null 2>&1 ;;
            inactive)     ros2 lifecycle set /slam_toolbox activate  > /dev/null 2>&1 ;;
            *)            sleep 2 ;;
        esac
    done
    if [ "${slam_state}" = "active" ]; then
        echo "[drive_test] slam_toolbox active"
    else
        echo "[drive_test] !! slam_toolbox activation FAILED — check ${LOG_DIR}/slam.log"
    fi
else
    echo "[drive_test] !! /slam_toolbox never registered — check ${LOG_DIR}/slam.log"
fi

# --- print connection info ------------------------------------------------

# Use the default-route source IP so we get whichever interface is actually
# routing to the outside — works on 192.168/*, 10/*, 172.16/12, Tailscale,
# ethernet-only setups etc., not just the earlier `/^192\./` regex.
IP=$(ip -4 route get 1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}')
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
