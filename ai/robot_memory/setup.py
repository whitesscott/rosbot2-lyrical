"""Combined pip / ament_python setup for robot_memory.

This file is authoritative for both build paths:

  * `pip install -e .`     -> populates the venv, registers `robot-map-*`
                              scripts on PATH.
  * `colcon build`         -> lays out share/ + lib/ so `ros2 run robot_memory
                              memory_node` and the launch file work.

pyproject.toml only declares the setuptools build backend; nothing else,
to avoid the two toolchains disagreeing on package metadata.
"""

from pathlib import Path

from setuptools import find_packages, setup

package_name = "robot_memory"
here = Path(__file__).parent
# colcon build stages setup.py into a build/ subdir but does NOT copy README.md,
# so guard the read. Falls back to the short description for pip's metadata.
_readme = here / "README.md"
long_description = _readme.read_text(encoding="utf-8") if _readme.exists() else ""

setup(
    name=package_name,
    version="0.1.0",
    description="Spatial memory for a ROS 2 mobile robot: VLM keyframe captioning + semantic query, on-device.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Scott Whites",
    maintainer="Scott Whites",
    maintainer_email="whitesscott@comcast.net",
    license="MIT",
    python_requires=">=3.10",

    packages=find_packages(include=[package_name, package_name + ".*"]),
    install_requires=[
        # torch intentionally not pinned: on Jetson we inherit the JetPack
        # build via `uv venv --system-site-packages`.
        "transformers>=4.45",
        "accelerate",
        "safetensors",
        "pillow",
        "sentence-transformers",
        "chromadb",
        "numpy",
        "einops",
        "setuptools",
    ],
    extras_require={"dev": ["pytest", "pytest-cov"]},

    # ament_python layout: resource marker + package.xml + launch/.
    data_files=[
        ("share/ament_index/resource_index/packages",
            ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/memory.launch.py"]),
    ],
    zip_safe=True,
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "robot-map-caption = robot_memory.captioner:main",
            "robot-map-query = robot_memory.query:main",
            "memory_node = robot_memory.nodes.memory_node:main",
        ],
    },
)
