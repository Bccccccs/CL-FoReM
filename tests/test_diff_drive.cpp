#include <modulation_rl/myutils.h>
#include <cassert>
#include <cmath>
#include <iostream>
int main() {
    for (double yaw : {0., 1.2, 3.13}) {
        for (double speed : {0., .15, -.15}) {
            for (double omega : {0., .4, -.4}) {
                tf::Transform start(tf::createQuaternionFromYaw(yaw), tf::Vector3(1.,2.,0.));
                auto goal=myutils::calcDesiredBaseTfDiffDrive(start,tf::Vector3(speed,0,0),omega,.1);
                tf::Vector3 velocity(9,9,9); double rotation=9;
                myutils::calcDesiredBaseCommandDiffDrive(start,goal,.1,velocity,rotation);
                assert(std::abs(velocity.x()-speed)<1e-8);
                assert(std::abs(velocity.y())<1e-8 && std::abs(velocity.z())<1e-8);
                assert(std::abs(rotation-omega)<1e-8);
            }
        }
    }
    std::cout << "27 signed differential-drive round trips passed\n";
}
