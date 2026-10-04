"""Standalone launch for the robot_memory node.

Usage on the Orin after both workspace overlays are sourced:

    ros2 launch robot_memory memory.launch.py

Override parameters at launch time:

    ros2 launch robot_memory memory.launch.py \
        image_topic:=/camera/image_raw \
        keyframe_distance_m:=0.5

Assumes the rest of the ROS stack (base + slam_toolbox for the map
frame, or at least the odom frame + a monocular image publisher) is
already running.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    args = [
        ("image_topic", "/image_raw"),
        ("map_frame", "map"),
        ("fallback_frame", "odom"),
        ("base_frame", "base_footprint"),
        ("keyframe_distance_m", "1.0"),
        ("keyframe_yaw_deg", "30.0"),
        ("worker_queue_size", "4"),
        ("caption_max_tokens", "80"),
    ]

    declared = [DeclareLaunchArgument(name, default_value=default) for name, default in args]

    node = Node(
        package="robot_memory",
        executable="memory_node",
        name="memory_node",
        output="screen",
        parameters=[{name: LaunchConfiguration(name) for name, _ in args}],
    )

    return LaunchDescription([*declared, node])
