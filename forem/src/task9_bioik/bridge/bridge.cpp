#include <ros/ros.h>
#include <pluginlib/class_loader.h>
#include <moveit/kinematics_base/kinematics_base.h>
#include <moveit/robot_model/robot_model.h>
#include <moveit/robot_state/robot_state.h>
#include <urdf_parser/urdf_parser.h>
#include <srdfdom/model.h>
#include <bio_ik/bio_ik.h>
#include <fstream>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <chrono>
#include <ctime>
std::string read(const char* p){std::ifstream f(p);std::stringstream s;s<<f.rdbuf();return s.str();}
int main(int argc,char**argv){
 ros::init(argc,argv,"task9_bioik_bridge",ros::init_options::NoSigintHandler | ros::init_options::AnonymousName);ros::NodeHandle nh;
 ros::console::set_logger_level(ROSCONSOLE_DEFAULT_NAME,ros::console::levels::Error);
 auto u=urdf::parseURDF(read(argv[1]));auto s=std::make_shared<srdf::Model>();s->initString(*u,read(argv[2]));
 auto model=std::make_shared<moveit::core::RobotModel>(u,s);
 nh.setParam("/robot_description_kinematics/manipulator/threads",1);
 nh.setParam("/robot_description_kinematics/manipulator/random_seed",471812);
 nh.setParam("/robot_description_kinematics/manipulator/mode","bio2_memetic");
 // initialize(model) uses empty robot_description; KinematicsBase looks under group param too.
 nh.setParam("/manipulator/threads",1);nh.setParam("/manipulator/random_seed",471812);nh.setParam("/manipulator/mode","bio2_memetic");
 pluginlib::ClassLoader<kinematics::KinematicsBase> loader("moveit_core","kinematics::KinematicsBase");
 auto ik=loader.createInstance("bio_ik/BioIKKinematicsPlugin");
 if(!ik->initialize(*model,"manipulator","ur5_base_link",std::vector<std::string>{"ur5_tool0"},0.005))return 3;
 int threads=0,seed=0;std::string mode;nh.getParam("/robot_description_kinematics/manipulator/threads",threads);nh.getParam("/robot_description_kinematics/manipulator/random_seed",seed);nh.getParam("/robot_description_kinematics/manipulator/mode",mode);std::cerr<<"CONFIGURED_PARAMS threads="<<threads<<" random_seed="<<seed<<" mode="<<mode<<std::endl;
 std::cerr<<"READY joints";for(auto&n:ik->getJointNames())std::cerr<<" "<<n;std::cerr<<std::endl;
 std::cout<<std::setprecision(17);std::string line;
 while(std::getline(std::cin,line)){
  std::istringstream in(line);char cmd;in>>cmd;std::vector<double> q(6);for(auto&v:q)in>>v;
  if(cmd=='F'){
   moveit::core::RobotState state(model);state.setToDefaultValues();state.setJointGroupPositions("manipulator",q);state.update();
   auto T=state.getGlobalLinkTransform("ur5_base_link").inverse()*state.getGlobalLinkTransform("ur5_tool0");
   std::cout<<"F";for(int i=0;i<4;i++)for(int j=0;j<4;j++)std::cout<<" "<<T(i,j);std::cout<<std::endl;continue;
  }
  double timeout;in>>timeout;geometry_msgs::Pose p;in>>p.position.x>>p.position.y>>p.position.z>>p.orientation.x>>p.orientation.y>>p.orientation.z>>p.orientation.w;
  bio_ik::BioIKKinematicsQueryOptions opts;opts.return_approximate_solution=true;
  // Explicit CBL-like soft regularizers; no collision callback or hidden branch replacement.
  opts.goals.emplace_back(new bio_ik::MinimalDisplacementGoal(1.0));opts.goals.emplace_back(new bio_ik::AvoidJointLimitsGoal(1.0));
  std::vector<double> out;moveit_msgs::MoveItErrorCodes error;
  auto start=std::chrono::steady_clock::now();auto cpu=std::clock();
  bool ok=ik->searchPositionIK(p,q,timeout,out,error,opts);
  double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();double cput=double(std::clock()-cpu)/CLOCKS_PER_SEC;
  std::cout<<"I "<<ok<<" "<<error.val<<" "<<wall<<" "<<cput<<" "<<out.size();for(auto v:out)std::cout<<" "<<v;std::cout<<std::endl;
 }
}
