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

#pragma once
#include <list>

class RuneResFilter {
public:
	RuneResFilter(int _filter_size = 5, int _shoot_time_gap = 100) 
		: filter_size(_filter_size + 1), shoot_time_gap(_shoot_time_gap), last_shoot_idx(-1), last_shoot_time(0){}
	bool setRecord(int record);
    void clear(){
        last_shoot_idx = -1;
        last_shoot_time = 0;
        history.clear();
    }

    /**
     * @brief getResult
     * @return true, if latest record has the most votes and the num of votes large than half of the size of history record
     */
	bool getResult();
	bool isShootable(double anglex, double angley, double z, int cell_idx);

private:
	std::list<int> history;
	int filter_size;
	int shoot_time_gap;
	int last_shoot_idx;
	int last_shoot_time;
};

class ArmorFilter {
public:
	ArmorFilter(int _filter_size = 5)
		: filter_size(_filter_size) {}

    void clear(){
        history.clear();
    }

    bool getResult(bool is_small){
        if (history.size() < filter_size){
            history.push_back(is_small);
        }
        else {
            history.push_back(is_small);
            history.pop_front();
        }

        int vote_cnt[2] = {0};
        for (std::list<bool>::const_iterator it = history.begin(); it != history.end(); ++it){
            *it == 0 ? ++vote_cnt[0] : ++vote_cnt[1];
        }

        if (vote_cnt[0] == vote_cnt[1])
            return is_small;
        return vote_cnt[0] > vote_cnt[1] ? 0 : 1;
    }

private:
	std::list<bool> history;
	int filter_size;
};

class Filter1D {
public:
    Filter1D(int _filter_size = 5){
        filter_size = _filter_size;
    }
    void setRecord(double record){
        if (history.size() < filter_size){
            history.push_back(record);
            return;
        }
        history.push_back(record);
        history.pop_front();
    }

    double getResult(){
        double value = 0.0;
        for (std::list<double>::const_iterator it = history.begin(); it != history.end(); ++it){
            value += *it;
        }
        return value/history.size();
    }
private:
    std::list<double> history;
    int filter_size;
};


class FilterZ {
public:
    FilterZ(double _update_rate, double _max_change_value = 20.0){
        update_rate = _update_rate;
        max_change_value = _max_change_value;
        res = 0.0;
    }
    double getResult(double record) {
        if (res < 10e-5 ){
            res = record;
            last_value = record;
            return res;
        }
        if (record - last_value > max_change_value)
            record = last_value + max_change_value;
        else if (last_value - record> max_change_value)
            record = last_value - max_change_value;

        res = res * (1.0 - update_rate) + update_rate * record;
        last_value = record;
        return res;
    }
    void clear(){
        res = 0.0;
    }
private:
    double max_change_value;
    double update_rate;
    double last_value;
    double res;
};

