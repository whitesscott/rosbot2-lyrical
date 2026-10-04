import os
from pathlib import Path
import launch_ros.actions
import launch
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction,LogInfo,
                            IncludeLaunchDescription, SetEnvironmentVariable)
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.parameter_descriptions import ParameterValue

def _robot_description(urdf_name):
    # robot_state_publisher no longer accepts a URDF file argument; it takes
    # the model as the robot_description parameter. Read lazily so only the
    # selected robot's file is opened.
    urdf_path = os.path.join(
        get_package_share_directory('wheeltec_robot_urdf'), 'urdf', urdf_name)
    return {'robot_description': ParameterValue(
        Command(['cat ', urdf_path]), value_type=str)}


def generate_launch_description():
#aaaaaaaaaaaakm
    mini_akm = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('mini_akm_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.125', '--y', '0', '--z', '0.1608', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.195', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    senior_akm = GroupAction([
    
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('senior_akm_robot.urdf')],),
            
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.26', '--y', '0', '--z', '0.228', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.34', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    top_akm_bs = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('top_akm_bs_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.53', '--y', '0', '--z', '0.228', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.51', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    top_akm_dl = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('top_akm_dl_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.497', '--y', '0', '--z', '0.228', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.58', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

#mmmmmmmmmmmmmmmec

    mini_mec = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('mini_mec_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.048', '--y', '0', '--z', '0.18', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.195', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    senior_mec_bs = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('senior_mec_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.1', '--y', '0', '--z', '0.165', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.18', '--y', '0', '--z', '0.3', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    senior_mec_dl = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('senior_mec_dl_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.165', '--y', '0', '--z', '0.235', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.255', '--y', '0', '--z', '0.35', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    top_mec_bs = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('top_mec_bs_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.155', '--y', '0', '--z', '0.195', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.24', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    top_mec_dl = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('top_mec_dl_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.155', '--y', '0', '--z', '0.195', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.24', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    senior_mec_EightDrive = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('mec_EightDrive_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.207', '--y', '0', '--z', '0.228', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.32', '--y', '0', '--z', '0.2', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    flagship_mec_bs_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('flagship_mec_bs_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.267', '--y', '0', '--z', '0.228', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.32', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    flagship_mec_dl_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('flagship_mec_dl_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.267', '--y', '0', '--z', '0.228', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.32', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
#oooooooooooooooooomi

    mini_omni = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('mini_omni_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.0', '--y', '0', '--z', '0.17', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.08', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    senior_omni = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('senior_omni_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.087', '--y', '0', '--z', '0.23', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.187', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    top_omni = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('top_omni_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.149', '--y', '0', '--z', '0.23', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.25', '--y', '0', '--z', '0.32', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

#dddddddddddddddddddiff

    mini_tank = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('mini_diff_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.02', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.14', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

#4444444444444444444wd
    mini_4wd = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('mini_4wd_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.031', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.12', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    
    senior_4wd_bs_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('senior_4wd_bs_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.02', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.14', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    
    senior_4wd_dl_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('senior_4wd_dl_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.02', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.14', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    
    flagship_4wd_bs_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('flagship_4wd_bs_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.02', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.14', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    flagship_4wd_dl_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('flagship_4wd_dl_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.02', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.14', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    top_4wd_bs_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('top_4wd_bs_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.02', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.14', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    top_4wd_dl_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('top_4wd_dl_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.02', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.14', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    
#dddddddddddddddddddiff
    mini_diff = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('mini_diff_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.031', '--y', '0', '--z', '0.155', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.12', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    senior_diff_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('senior_diff_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.087', '--y', '0', '--z', '0.195', '--yaw', '3.1415', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.12', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    four_wheel_diff_bs = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('four_wheel_diff_bs_robot.urdf')],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.157', '--y', '0', '--z', '0.385', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.08', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    four_wheel_diff_dl = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('four_wheel_diff_dl_robot.urdf')],),
            
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.272', '--y', '0', '--z', '0.257', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.08', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    brushless_senior_diff = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('brushless_senior_diff.urdf')],),
            
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.272', '--y', '0', '--z', '0.257', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.08', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])

    flagship_four_wheel_diff_bs_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('flagship_four_wheel_diff_bs_robot.urdf')],),
            
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.272', '--y', '0', '--z', '0.257', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.08', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    
    flagship_four_wheel_diff_dl_robot = GroupAction([
        launch_ros.actions.Node(
            package='robot_state_publisher', 
            executable='robot_state_publisher', 
            name='robot_state_publisher',
            parameters=[_robot_description('flagship_four_wheel_diff_dl_robot.urdf')],),
            
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_laser',
            arguments=['--x', '0.272', '--y', '0', '--z', '0.257', '--yaw', '3.14', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'laser_link'],),
        launch_ros.actions.Node(
            package='tf2_ros', 
            executable='static_transform_publisher', 
            name='base_to_camera',
            arguments=['--x', '0.08', '--y', '0', '--z', '0.25', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_footprint', '--child-frame-id', 'camera_link'],),
    ])
    # Create the launch description and populate
    ld = LaunchDescription()

    #Select your car model here, the options are:
    #mini_akm, senior_akm, top_akm_bs, top_akm_dl, 
    #mini_mec, senior_mec_bs, senior_mec_dl, top_mec_bs, top_mec_dl, senior_mec_EightDrive, flagship_mec_bs_robot,flagship_mec_dl_robot, 
    #mini_omni, senior_omni, top_omni, 
    #mini_tank,
    #mini_4wd,senior_4wd_bs_robot,senior_4wd_dl_robot,flagship_4wd_bs_robot,flagship_4wd_dl_robot,top_4wd_bs_robot,top_4wd_dl_robot
    #mini_diff, senior_diff_robot,four_wheel_diff_bs ,four_wheel_diff_dl, brushless_senior_diff,flagship_four_wheel_diff_bs_robot,flagship_four_wheel_diff_dl_robot
    ld.add_action(mini_akm)
    return ld

