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

#include "Predictor.hpp"
#include "opencv2/opencv.hpp"
#include <algorithm>
using namespace std;
using namespace cv;
bool Predictor::setRecord(double value, double time){
    if (history_value.size() < history_size){
        history_time.push_back(time);
        history_value.push_back(value);
    }
    else {
        history_time.push_back(time);
        history_value.push_back(value);
        history_time.pop_front();
        history_value.pop_front();
    }
}

double Predictor::predict(double time){
    list<double>::const_iterator it_in = history_time.begin();
    double latest_value = history_value.back();
    if(abs(latest_value) < 5.0 || history_value.size() < history_size)
        return latest_value;
    if(history_time.back() - *it_in > 150.0)
        return latest_value;
    list<double>::const_iterator it_out = history_value.begin();
    list<double>::const_iterator prev_out = it_out;
    double max_o = -500000, min_o = 500000;
    for(list<double>::const_iterator it = it_out, it_i = it_in; it != history_value.end(); ++it, ++it_i){
        if(max_o < *it)
            max_o = *it;
        if(min_o > *it)
            min_o = *it;
        if(abs(*it - *prev_out) > 5.0){
            return latest_value;
        }
        prev_out = it;
        //printf("(%2f,%2f) ", *it, *it_i);
    }
   // printf("\n");
    if (max_o - min_o < 3.0)      // angle gap must lager than 3 degree
        return latest_value;

    Mat A(history_size,3,CV_64F);
    Mat b(history_size,1,CV_64F);
    double * b_data = (double *) b.data;
    double * A_data = (double *) A.data;

    for (; it_in != history_time.end(); ++A_data, ++b_data, ++it_in, ++it_out){
        *A_data = (*it_in-time) * (*it_in-time);
        *(++A_data) = (*it_in-time);
        *(++A_data) = 1;
        *b_data = *it_out;
    }

    // A*w = b  =>  w = (A_t * A).inverse * b
    Mat A_t = A.t();
    Mat w = (A_t*A).inv()*A_t * b;
    Mat q = (Mat_<double>(1,3) << 0, 0, 1);
    Mat ret = q*w;

    double predict_angel = ret.at<double>(0);
    const double max_gap = 3.0;
    if(predict_angel - latest_value > max_gap)
        predict_angel = latest_value + max_gap;
    else if(predict_angel - latest_value < -max_gap)
        predict_angel = latest_value - max_gap;
    return predict_angel;

}

