cmake_minimum_required(VERSION 3.0.2)
project(forem_husky)

find_package(catkin REQUIRED)
catkin_package()

install(DIRECTORY launch worlds urdf
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

catkin_install_python(PROGRAMS scripts/pose_bridge.py scripts/pose_gate.py scripts/task4_input_adapter.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
