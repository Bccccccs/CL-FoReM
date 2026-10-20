// Isolated diagnostic against the actual unmodified official ov_core library.
// argv: total initialization features; manifest lines: original_stamp left.png right.png.
#include <iostream>
#include <fstream>
#include "track/TrackKLT.h"
#include "cam/CamRadtan.h"
#include "feat/FeatureHelper.h"
#include <opencv2/imgcodecs.hpp>
int main(int argc,char**argv){
 if(argc<3||argc>5)return 2;
 std::unordered_map<size_t,std::shared_ptr<ov_core::CamBase>> cams;
 for(size_t id=0;id<2;id++){
  cams[id]=std::make_shared<ov_core::CamRadtan>(640,480);
  Eigen::VectorXd p(8);p<<319.9988245765257,319.9988245765257,320.5,240.5,0,0,0,0;cams[id]->set_value(p);
 }
 auto histogram=(argc==5&&std::string(argv[4])=="NONE")?ov_core::TrackBase::NONE:ov_core::TrackBase::HISTOGRAM;
 ov_core::TrackKLT tracker(cams,std::stoi(argv[1])/2,1024,true,histogram,20,5,5,argc>=4?std::stoi(argv[3]):10);
 std::ifstream input(argv[2]);double stamp;std::string left,right;
 while(input>>stamp>>left>>right){
  ov_core::CameraData m;m.timestamp=stamp;m.sensor_ids={0,1};m.images={cv::imread(left,cv::IMREAD_GRAYSCALE),cv::imread(right,cv::IMREAD_GRAYSCALE)};
  if(m.images[0].empty()||m.images[1].empty())return 3;
  m.masks={cv::Mat::zeros(480,640,CV_8UC1),cv::Mat::zeros(480,640,CV_8UC1)};
  tracker.feed_new_camera(m);double newest=-1;
  for(const auto& f:tracker.get_feature_database()->get_internal_data())for(const auto& c:f.second->timestamps)for(double t:c.second)newest=std::max(newest,t);
  int n0=0,n1=0;double av0=0,av1=0,var0=0,var1=0;
  if(newest>=0){ov_core::FeatureHelper::compute_disparity(tracker.get_feature_database(),av0,var0,n0,newest-1.0);ov_core::FeatureHelper::compute_disparity(tracker.get_feature_database(),av1,var1,n1,newest,newest-1.0);}
  std::cout<<"PROBE "<<stamp<<" "<<tracker.get_last_obs()[0].size()<<" "<<tracker.get_last_obs()[1].size()<<" "<<tracker.get_feature_database()->get_internal_data().size()<<" "<<newest<<" "<<n0<<" "<<n1<<std::endl;
  for(const auto& cam:tracker.get_last_obs())for(const auto& pt:cam.second)std::cout<<"POINT "<<stamp<<" "<<cam.first<<" "<<pt.pt.x<<" "<<pt.pt.y<<std::endl;
 }
 return 0;
}
