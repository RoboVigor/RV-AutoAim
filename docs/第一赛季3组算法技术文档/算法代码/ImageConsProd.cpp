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
#include "Predictor.hpp"
#include "RuneDetector.hpp"
#include "RuneResFilter.hpp"
#include "AngleSolver.hpp"
#include "RMVideoCapture.hpp"
#include "serial.h"
#include "LedController.hpp"

using namespace std;

//#define USE_VIDEO

#define VIDEO_WIDTH  1280
#define VIDEO_HEIGHT 720
#define BUFFER_SIZE 1
volatile unsigned int prdIdx;
volatile unsigned int csmIdx;
struct ImageData {
    Mat img;
    unsigned int frame;
};

ImageData data[BUFFER_SIZE];

enum Video_Mode {
    FRAME_NONE = 0,
    FRAME_720_60 = 1,
    FRAME_480_30 = 2,
    FRAME_480_120 = 3
};
volatile Video_Mode cur_video_mode = VIDEO_HEIGHT == 720 ? FRAME_720_60 : FRAME_480_120;

void cvtRect(const cv::RotatedRect & rect, const Point2f & center1, cv::RotatedRect & cvted_rect, const Point2f & center2, double scale){
    cv::Size s(rect.size.width * scale, rect.size.height * scale);
    cv::Point2f c = (rect.center - center1) * scale + center2;
    cvted_rect = cv::RotatedRect(c, s, rect.angle);
}

void ImageConsProd::ImageProducer(){
    // set input source and image size
#ifdef USE_VIDEO
    settings->save_result = 0;
    string video_name = "/home/ubuntu/projects/RMVision/build-RMVision-Desktop-Release/webcam.avi";
    //string video_name = "/home/ubuntu/projects/RMVision/RMVision/20160823165244.mp4";
    VideoCapture cap(video_name); // open the default camera
    if (!cap.isOpened())  // check if we succeeded
        return;
#else
    RMVideoCapture cap("/dev/video0", 3);
    cap.setVideoFormat(VIDEO_WIDTH, VIDEO_HEIGHT, 1);
    cap.setExposureTime(0, 64);//settings->exposure_time);
    cap.startStream();
    cap.info();
#endif

    Video_Mode last_video_mode = FRAME_NONE;
    while(1){
        //int t1 = cv::getTickCount();
        //cout << "resolution720: " << resolution720 << "\tmode: " << settings->mode << endl;
#ifndef USE_VIDEO
        if (cur_video_mode != last_video_mode){
            last_video_mode = cur_video_mode;
            if(cur_video_mode == FRAME_720_60){
                cap.changeVideoFormat(1280, 720, 1);
                cap.setExposureTime(0, 64);//76);
                cap.info();
            }
            else if (cur_video_mode == FRAME_480_30){
                cap.changeVideoFormat(640, 480, 0);
                cap.setExposureTime(0, 79);
                cap.info();
            }
            else if (cur_video_mode == FRAME_480_120){
                cap.changeVideoFormat(640, 480, 1);
                cap.setExposureTime(0, 64);
                //cap.setExposureTime(0, 96);
                cap.info();
            }
        }
#endif
        while(prdIdx - csmIdx >= BUFFER_SIZE);
        //int t1 = cv::getTickCount();
        cap >> data[prdIdx % BUFFER_SIZE].img;
#ifndef USE_VIDEO
        data[prdIdx % BUFFER_SIZE].frame = cap.getFrameCount();
#else
        data[prdIdx % BUFFER_SIZE].frame++;
#endif
        //int t2 = cv::getTickCount();
        //cout << "Producer-Time: " << (t2 - t1) * 1000.0 / cv::getTickFrequency() << "ms\n";
        ++prdIdx;
    }
}

void ImageConsProd::ImageConsumer(){
    Settings & setting = *settings;

    // load calibration parameter
    FileStorage fs(setting.intrinsic_file_480, FileStorage::READ);
    if (!fs.isOpened())	{
        cout << "Could not open the configuration file: \"" << setting.intrinsic_file_480 << "\"" << endl;
        return ;
    }
    Mat cam_matrix_480, distortion_coeff_480;
    fs["Camera_Matrix"] >> cam_matrix_480;
    fs["Distortion_Coefficients"] >> distortion_coeff_480;

    FileStorage fs1(setting.intrinsic_file_720, FileStorage::READ);
    if (!fs1.isOpened())	{
        cout << "Could not open the configuration file: \"" << setting.intrinsic_file_720 << "\"" << endl;
        return ;
    }
    Mat cam_matrix_720, distortion_coeff_720;
    fs1["Camera_Matrix"] >> cam_matrix_720;
    fs1["Distortion_Coefficients"] >> distortion_coeff_720;

    AngleSolver solver_480(cam_matrix_480, distortion_coeff_480, 21.6, 5.4, settings->scale_z_480, settings->min_detect_distance, settings->max_detect_distance);
    AngleSolver solver_720(cam_matrix_720, distortion_coeff_720, 21.6, 5.4, settings->scale_z, settings->min_detect_distance, settings->max_detect_distance);

    Point2f image_center_480 = Point2f(cam_matrix_480.at<double>(0,2), cam_matrix_480.at<double>(1,2));
    Point2f image_center_720 = Point2f(cam_matrix_720.at<double>(0,2), cam_matrix_720.at<double>(1,2));

    // parameter of PTZ and barrel
    const double overlap_dist = 100000.0;
    const double barrel_ptz_offset_y = 3.3;
    const double ptz_camera_y = 0.8;
    const double ptz_camera_z = -20.5;
    //const double ptz_camera_z = -10.5;
    double theta = -atan((ptz_camera_y + barrel_ptz_offset_y)/overlap_dist);
    double r_data[] = {1,0,0,0,cos(theta),-sin(theta), 0, sin(theta), cos(theta)};
    double t_data[] = {0, ptz_camera_y, ptz_camera_z}; // ptz org position in camera coodinate system
    Mat t_camera_ptz(3,1, CV_64FC1, t_data);
    Mat r_camera_ptz(3,3, CV_64FC1, r_data);
    solver_480.setRelationPoseCameraPTZ(r_camera_ptz, t_camera_ptz, barrel_ptz_offset_y);
    solver_720.setRelationPoseCameraPTZ(r_camera_ptz, t_camera_ptz, barrel_ptz_offset_y);

    AngleSolverFactory angle_slover;
    angle_slover.setTargetSize(21.6, 5.4, AngleSolverFactory::TARGET_ARMOR);
    angle_slover.setTargetSize(12.4, 5.4, AngleSolverFactory::TARGET_SAMLL_ATMOR);
    angle_slover.setTargetSize(28.0, 16.0, AngleSolverFactory::TARGET_RUNE);
    //angle_slover.setTargetSize(15.0, 9.2, AngleSolverFactory::TARGET_RUNE); // for srceen debug

    Predictor predictor;
    // load armor detector template
    ArmorDetector armor_detector(setting.armor);
    Mat template_img = imread(setting.template_image_file);
    Mat small_template_img = imread(setting.small_template_image_file);
    armor_detector.initTemplate(template_img, small_template_img);
    armor_detector.setPnPSlover(&solver_480, &solver_720);
    FilterZ filter_z(0.1);
    ArmorFilter armor_filter(7);

    // rune detection
    const Settings::RuneParam & rparm = setting.rune;
    RuneDetector rune_detector(rparm.sudoku_cell_width, rparm.sudoku_cell_height, true, RuneDetector::RUNE_CANNY);
    RuneResFilter filter(rparm.shoot_filter_size, rparm.shoot_time_gap);

    // vars for debug use
    LedController led("/sys/class/gpio/gpio158/value");
    led.ledON();
    Mat src_csm;
    int t1 = 0, t2 = 0;
#ifdef USE_VIDEO
    setting.save_result = 0;
#endif
    VideoWriter vw, vw_src;
    if (setting.save_result > 0){      
        vw.open("webcam.avi", CV_FOURCC('M', 'J', 'P', 'G'), 30, cv::Size(VIDEO_WIDTH, VIDEO_HEIGHT), true);
        vw_src.open("webcam_src.avi", CV_FOURCC('M', 'J', 'P', 'G'), 30, cv::Size(VIDEO_WIDTH, VIDEO_HEIGHT), true);
        if (vw.isOpened() == false || vw_src.isOpened() == false){
            cout << "can't open *.avi file" << endl;
            return;
        }
    }

    // process loop
    const double offset_anlge_x = 0;
    const double offset_anlge_y = 0;
    double resolution_change_threshold = 200.0;
    Mat src;
    int frame_num = 0;
    int miss_detection_cnt = 0;
    int last_rune_idx = -1;
    int last_rune_timestamp = 0;
    bool flash_flag = false;
    while(1){
        // waiting for image data ready
        while(prdIdx - csmIdx == 0);
        data[csmIdx % BUFFER_SIZE].img.copyTo(src);
        frame_num = data[csmIdx % BUFFER_SIZE].frame;
        ++csmIdx;

        if(setting.show_image || setting.save_result){
            t1 = cv::getTickCount();
            src.copyTo(src_csm);
        }

        RotatedRect rect;
        double angle_x = 0.0, angle_y = 0.0;
        double send_data[3] = {0};
        if (setting.mode == ARMOR_MODE){  // armor detection mode
            if (cur_video_mode == FRAME_480_30 || cur_video_mode == FRAME_NONE)
                cur_video_mode = FRAME_720_60;
            if (!((cur_video_mode == FRAME_480_120 && src.rows == 480) || (cur_video_mode == FRAME_720_60 && src.rows == 720)))
                continue;

            if (src.rows == 480){
                armor_detector.setPara(setting.armor);
                angle_slover.setSolver(&solver_480);
            }
            else if(src.rows == 720){
                ArmorParam armor_para_720 = setting.armor;
                armor_para_720.max_light_delta_h = 700;
                armor_para_720.min_light_height = 8;
                armor_para_720.min_light_delta_h = 20;
                armor_para_720.avg_contrast_threshold = 90;
                armor_detector.setPara(armor_para_720);
                angle_slover.setSolver(&solver_720);
            }

            armor_detector.setPitchAngle(other_param->angle_pitch);
            rect = armor_detector.getTargetAera(src);
            bool is_small = armor_filter.getResult(armor_detector.isSamllArmor());
            AngleSolverFactory::TargetType type = is_small ? AngleSolverFactory::TARGET_SAMLL_ATMOR : AngleSolverFactory::TARGET_ARMOR;

            if (angle_slover.getAngle(rect, type, angle_x, angle_y, setting.bullet_speed, other_param->angle_pitch) == true){
                miss_detection_cnt = 0;
                // using history data to predict the motion
                predictor.setRecord(angle_x, frame_num);
                double z = angle_slover.getSolver().position_in_camera.at<double>(2,0);
                double angle_x_predict = predictor.predict(frame_num + 1.0);
                send_data[0] = (angle_x_predict + offset_anlge_x) * 100;
                send_data[1] = (angle_y + offset_anlge_y) * 100;
                send_data[2] = (cur_video_mode == FRAME_720_60) ? 2 : 1;
                //send_data[2] = z;

                // send data to car
                sendXYZ(fd2car, send_data);
                cout <<"Armor Type: " << (type == AngleSolverFactory::TARGET_ARMOR ? "Large\n" : "Small\n") << "Armor Size: " << rect.size << "\n";
                cout << send_data[0] << ", " << send_data[1] << ", "  << send_data[2] << endl;
                cout << "xyz in camera: " << angle_slover.getSolver().position_in_camera.t() << endl;
#ifndef USE_VIDEO
                if(setting.save_result == 0){
                    double avg_z = filter_z.getResult(z);
                    if (cur_video_mode == FRAME_480_120 && avg_z > resolution_change_threshold){
                        cur_video_mode = FRAME_720_60;
                        resolution_change_threshold -= 80.0;
                        const RotatedRect & last_rect = armor_detector.getLastResult();
                        RotatedRect s_last_rect;
                        cvtRect(last_rect, cv::Point2f(320, 240), s_last_rect, cv::Point2f(640, 360), 2.0);
                        armor_detector.setLastResult(s_last_rect);
                        cout << "capture mode changed : FRAME_720_60   threshold: " << resolution_change_threshold
                             << "\t avg z: " << avg_z << "\n";
                    }
                    else if (cur_video_mode == FRAME_720_60 && avg_z < resolution_change_threshold){
                        cur_video_mode = FRAME_480_120;
                        resolution_change_threshold += 80.0;
                        const RotatedRect & last_rect = armor_detector.getLastResult();
                        RotatedRect s_last_rect;
                        cvtRect(last_rect, cv::Point2f(640, 360), s_last_rect, cv::Point2f(320, 240), 0.5);
                        armor_detector.setLastResult(s_last_rect);
                        cout << "capture mode changed : FRAME_480_120   threshold: " << resolution_change_threshold
                             << "\t avg z: " << avg_z << "\n";
                    }
                }
#endif
                led.ledflash(25);
            }
            else {
                ++miss_detection_cnt;
                if (miss_detection_cnt > 10){
                    led.ledOFF();
                    filter_z.clear();
                }
                if(miss_detection_cnt > 120 && cur_video_mode == FRAME_480_120){
                    cur_video_mode = FRAME_720_60;
                    resolution_change_threshold -= 80.0;
                }

                sendXYZ(fd2car, send_data);
            }
        }// end armor detection mode

        else if (setting.mode == RUNE_MODE){      //rune system
            cur_video_mode = FRAME_480_30;
            angle_slover.setSolver(&solver_480);
            if(src.rows != 480)
                continue;
            pair<int, int> res = rune_detector.getTarget(src);
            if (filter.setRecord(res.second) && filter.getResult())	{
                rect = rune_detector.getRect(res.first);
                if (angle_slover.getAngle(rect, AngleSolverFactory::TARGET_RUNE, angle_x, angle_y, setting.bullet_speed, other_param->angle_pitch) == true){
                    send_data[0] = (angle_x + offset_anlge_x) * 100;
                    send_data[1] = (angle_y + offset_anlge_y) * 100;
                    send_data[2] = res.second + 1;

                    if (last_rune_idx != send_data[2]){
                        int cur_timestamp = cv::getTickCount();
                        if ((cur_timestamp - last_rune_timestamp)* 1000.0 / cv::getTickFrequency() < 500.0)
                            flash_flag = true;
                        else
                            flash_flag = false;
                        last_rune_timestamp = cur_timestamp;
                        last_rune_idx = send_data[2];
                    }
                    if(flash_flag == false)
                        sendXYZ(fd2car, send_data);

                    //cout << "xyz:" << solver.position_in_camera.t() <<endl;
                    cout << send_data[0] << ", " << send_data[1] << ", "  << send_data[2] << endl;

                    led.ledflash(25);
                }
            }
            else if ((setting.show_image > 0 || setting.save_result > 0) && res.first >=0){
                RotatedRect rect_filtered = rune_detector.getRect(res.first);
                rectangle(src_csm, rect_filtered.boundingRect(), CV_RGB(255, 0, 0), 3);
            }

            // count out of view range
            if (res.first >=0){
                miss_detection_cnt = 0;
            }
            else {
                ++miss_detection_cnt;
                if (miss_detection_cnt >= 5){
                    sendXYZ(fd2car, send_data);
                    led.ledOFF();
                }
            }
        }// end rune system
        else {
            led.ledON();
            miss_detection_cnt = 0;
            last_rune_idx = -1;
            last_rune_timestamp = 0;
            flash_flag = false;
            filter.clear();
            predictor.clear();
            filter_z.clear();
            armor_detector.reset();
        }

        // other pc's serial debug
        //sendData(arg, (char *)str, strlen(str), INFO);

        // draw result
        if(setting.show_image > 0 || setting.save_result > 0){
            // show center and result
            cv::Point2f & image_center = src_csm.rows == 720 ? image_center_720 : image_center_480;
            circle(src_csm, image_center, 3, CV_RGB(0, 255, 0), 2);

            Point2f vertices[4];
            rect.points(vertices);
            for (int i = 0; i < 4; i++){
                line(src_csm, vertices[i], vertices[(i + 1) % 4], CV_RGB(0, 255, 0), 3);
            }

            char str[30];
            sprintf(str, "%.1f, %.1f, %.1f", send_data[0], send_data[1], send_data[2]);
            putText(src_csm, str, Point(10, 40), CV_FONT_HERSHEY_COMPLEX_SMALL, 1.3, CV_RGB(128, 255, 0), 1);
            t2 = cv::getTickCount();
            cout << "Consumer-Time: " << (t2 - t1) * 1000.0 / cv::getTickFrequency() << "ms   frame No.:" << frame_num << endl;
        }

        if (setting.show_image > 0){
            Mat src_show = src_csm;
            if (src_csm.rows == 720)
                resize(src_csm, src_show, Size(640,360));
            imshow("result", src_show);

#ifdef USE_VIDEO
            waitKey(0);
#else
            char key = waitKey(1);
            // debug use
            if (key == 'a')
                setting.mode = RUNE_MODE;
            else if (key == 's')
                setting.mode = ARMOR_MODE;
            else if (key == 'd')
                cur_video_mode = FRAME_480_120;
            else if (key == 'f')
                cur_video_mode = FRAME_720_60;
#endif
        }

        if (setting.save_result > 0){
            vw << src;
            vw_src << src_csm;
        }
    }
}

