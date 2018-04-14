/*******************************************************************************************************************
Copyright 2017 Dajiang Innovations Technology Co., Ltd (DJI)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files(the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and / or sell copies of the Software, and 
to permit persons to whom the Software is furnished to do so, subject to the following conditions : 

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
*******************************************************************************************************************/

#include "ImageConsProd.hpp"
#include "RemoteController.hpp"
#include "Settings.hpp"
#include "serial.h"

#include <thread>
#include <unistd.h>
#include "RMVideoCapture.hpp"
#include "opencv2/highgui.hpp"
#include <iostream>

using namespace cv;
using namespace std;
int adjustExposure(){
    RMVideoCapture cap("/dev/video0", 3);
    cap.setVideoFormat(1280, 720, 1);
    int exp_t = 64;
    cap.setExposureTime(0, exp_t);//settings->exposure_time);
    cap.startStream();
    cap.info();
    while(1){
        Mat src;
        cap >> src;
        imshow("src", src);
        char key = waitKey(20);
        if (key == 'w'){
            exp_t += 1;
            cap.setExposureTime(0, exp_t);//settings->exposure_time);
            cout << "current exp t:\t" << exp_t << endl;
        }
        else if(key == 's'){
            exp_t -= 1;
            cap.setExposureTime(0, exp_t);
            cout << "current exp t:\t" << exp_t << endl;
        }
    }
}


int main(int argc, char * argv[]){
    //adjustExposure();

    char * config_file_name = "/home/ubuntu/projects/RMVision/RMVision/param_config.xml";
    if (argc > 1)
        config_file_name = argv[1];
    Settings setting(config_file_name);
    OtherParam other_param;
    // communicate with car
    int fd2car = openPort("/dev/ttyTHS2");
    configurePort(fd2car);

    // start threads
    ImageConsProd image_cons_prod(&setting, &other_param, fd2car);
    std::thread t1(&ImageConsProd::ImageProducer, image_cons_prod); // pass by reference
    std::thread t2(&ImageConsProd::ImageConsumer, image_cons_prod);

    // debug use
    RemoteController controller(&setting, &other_param, fd2car);
    std::thread t3(&RemoteController::paraReceiver, controller);

    t1.join();
    t2.join();
    t3.join();
    close(fd2car);
}


//#include "RMVideoCapture.hpp"
//#include "opencv2/highgui.hpp"
//#include <iostream>
//
//using namespace cv;
//int adjustExposure(){
//    RMVideoCapture cap("/dev/video0", 3);
//    cap.setVideoFormat(640, 480, 0);
//    int exp_t = 30;
//    cap.setExposureTime(0, exp_t);//settings->exposure_time);
//    cap.startStream();
//    cap.info();
//    while(1){
//        Mat src;
//        cap >> src;
//        imshow("src", src);
//        char key = waitKey(20);
//        if (key == 'w'){
//            exp_t += 1;
//            cap.setExposureTime(0, exp_t);//settings->exposure_time);
//            cout << "current exp t:\t" << exp_t << endl;
//        }
//        else if(key == 's'){
//            exp_t -= 1;
//            cap.setExposureTime(0, exp_t);
//            cout << "current exp t:\t" << exp_t << endl;
//        }
//    }
//}

