cmake_minimum_required(VERSION 3.0.2)
project(forem_sim)

find_package(catkin REQUIRED)
catkin_package()

install(DIRECTORY launch urdf worlds
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

catkin_install_python(PROGRAMS scripts/start_controllers.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
