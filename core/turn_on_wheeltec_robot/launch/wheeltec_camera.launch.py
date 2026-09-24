import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # OrbbecSDK_ROS2 groups classic Astra / Astra Pro / Astra S under astra.launch.py.
    # For an Astra 2 (newer model) switch to astra2.launch.py; for a Gemini use gemini*.launch.py.
    orbbec_launch_dir = os.path.join(
        get_package_share_directory('orbbec_camera'), 'launch'
    )

    astra = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(orbbec_launch_dir, 'astra.launch.py')
        )
    )

    ld = LaunchDescription()
    ld.add_action(astra)
    return ld
