cmake_minimum_required(VERSION 2.8.3)
project(husky_control)

find_package(catkin REQUIRED COMPONENTS roslaunch)

catkin_package()

install(DIRECTORY config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
