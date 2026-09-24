import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    lslidar_launch_dir = os.path.join(
        get_package_share_directory('lslidar_driver'), 'launch'
    )

    m10_uart = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(lslidar_launch_dir, 'lsm10_uart_launch.py')
        )
    )

    ld = LaunchDescription()
    ld.add_action(m10_uart)
    return ld
