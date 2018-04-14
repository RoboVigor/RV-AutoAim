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

#include "RuneResFilter.hpp"
#include "opencv2/core/core.hpp"

bool RuneResFilter::setRecord(int record){
	if (record < 0) return false;
	if (history.size() < filter_size){
		history.push_back(record);
		return true;
	}
	history.push_back(record);
	history.pop_front();
	return true;
}

bool RuneResFilter::getResult(){
	int min_votes = (filter_size >> 1);
	if (history.size() < min_votes){
		return false;
	}

	int cur_record = history.back();
	int vote_cnt[9] = {0};
    for (std::list<int>::const_iterator it = history.begin(); it != history.end(); ++it){
		++vote_cnt[*it];
	}

	for (size_t i = 0; i < 9; i++) {
		if (vote_cnt[i] > min_votes && cur_record == i){
			return true;
		}
	}
	return false;
}

bool RuneResFilter::isShootable(double anglex, double angley, double z, int cell_idx){
    double in_angle_x = 1.5 * atan(14.0 / z) * 180.0 * 100 / 3.14159;
    double in_angle_y = 1.5 * atan(8.0 / z) * 180.0 * 100 / 3.14159;

	if (abs(anglex) < in_angle_x && abs(angley) < in_angle_y ){
		int cur_t = cv::getTickCount();
		if (cell_idx == last_shoot_idx){
			if ((cur_t - last_shoot_time) * 1000 / cv::getTickFrequency() > shoot_time_gap){
				last_shoot_time = cur_t;
				return true;
			}
		}
		else{
			last_shoot_idx = cell_idx;
			last_shoot_time = cur_t;
			return true;
		}
	}
	return false;
}

