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
#include "opencv2/core/core.hpp"
#include <string>
#include "ArmorDetector.hpp"

using namespace cv;

#define ARMOR_MODE 0
#define RUNE_MODE 1

struct OtherParam {
    OtherParam():angle_pitch(0.0){}
    double angle_pitch;
};

class Settings {
public:
	struct RuneParam {
		int sudoku_cell_width;
		int sudoku_cell_height;
		int shoot_time_gap;
		int shoot_filter_size;
        RuneParam(){
            sudoku_cell_width = 143;
            sudoku_cell_height = 81;
            shoot_time_gap = 100;
            shoot_filter_size = 5;
        }
	};

    Settings(const std::string & filename){
        scale_z_480 = 1.0;
        scale_z = 1.0;
        FileStorage setting_fs(filename, FileStorage::READ);
        read(setting_fs);
        setting_fs.release();
    }

	void read(const FileStorage& fs)  {
        // for debug image
        fs["show_image"] >> show_image;
        fs["save_result"] >> save_result;

		// for rune system
		fs["sudoku_cell_width"] >> rune.sudoku_cell_width;
		fs["sudoku_cell_height"] >> rune.sudoku_cell_height;
		fs["shoot_time_gap"] >> rune.shoot_time_gap;
		fs["shoot_filter_size"] >> rune.shoot_filter_size;

		// for armor system
		fs["min_light_gray"] >> armor.min_light_gray;
		fs["min_light_height"] >> armor.min_light_height;
		fs["avg_contrast_threshold"] >> armor.avg_contrast_threshold;
		fs["light_slope_offset"] >> armor.light_slope_offset;
		fs["max_light_delta_h"] >> armor.max_light_delta_h;
		fs["min_light_delta_h"] >> armor.min_light_delta_h;
		fs["max_light_delta_v"] >> armor.max_light_delta_v;
		fs["max_light_delta_angle"] >> armor.max_light_delta_angle;
		fs["avg_board_gray_threshold"] >> armor.avg_board_gray_threshold;
		fs["avg_board_grad_threshold"] >> armor.avg_board_grad_threshold;
		fs["grad_threshold"] >> armor.grad_threshold;
		fs["br_threshold"] >> armor.br_threshold;
        fs["enemy_color"] >> armor.enemy_color;

        fs["min_detect_distance"] >> min_detect_distance;
        fs["max_detect_distance"] >> max_detect_distance;

        // for camerar
        fs["intrinsic_file_480"] >> intrinsic_file_480;
        fs["intrinsic_file_720"] >> intrinsic_file_720;
        fs["exposure_time"] >> exposure_time;

        // for armor template
        fs["template_image_file"] >> template_image_file;
        fs["small_template_image_file"] >> small_template_image_file;

        // for system mode
        fs["mode"] >> mode;

        fs["bullet_speed"] >> bullet_speed;
        fs["scale_z"] >> scale_z;
        fs["scale_z_480"] >> scale_z_480;
		check();
	}

	void check(){
		ArmorParam default_armor;
		if (armor.min_light_gray < 5)
			armor.min_light_gray = default_armor.min_light_gray;
		if (armor.min_light_height < 5)
			armor.min_light_height = default_armor.min_light_height;
		if (armor.avg_contrast_threshold < 5)
			armor.avg_contrast_threshold = default_armor.avg_contrast_threshold;
		if (armor.light_slope_offset < 5)
			armor.light_slope_offset = default_armor.light_slope_offset;
		if (armor.max_light_delta_h < 5)
			armor.max_light_delta_h = default_armor.max_light_delta_h;
		if (armor.min_light_delta_h < 5)
			armor.min_light_delta_h = default_armor.min_light_delta_h;
		if (armor.max_light_delta_v < 5)
			armor.max_light_delta_v = default_armor.max_light_delta_v;
		if (armor.max_light_delta_angle < 5)
			armor.max_light_delta_angle = default_armor.max_light_delta_angle;
		if (armor.avg_board_gray_threshold < 5)
			armor.avg_board_gray_threshold = default_armor.avg_board_gray_threshold;
		if (armor.avg_board_grad_threshold < 5)
			armor.avg_board_grad_threshold = default_armor.avg_board_grad_threshold;
		if (armor.grad_threshold < 5)
			armor.grad_threshold = default_armor.grad_threshold;
		if (armor.br_threshold < 5)
			armor.br_threshold = default_armor.br_threshold;

        if(min_detect_distance < 10e-5)
            min_detect_distance = 50.0;
        if(max_detect_distance < 10e-5)
            max_detect_distance = 600.0;

		RuneParam default_rune;
		if (rune.sudoku_cell_width < 5)
			rune.sudoku_cell_width = default_rune.sudoku_cell_width;
		if (rune.sudoku_cell_height < 5)
			rune.sudoku_cell_height = default_rune.sudoku_cell_height;
		if (rune.shoot_time_gap < 5)
			rune.shoot_time_gap = default_rune.shoot_time_gap;
		if (rune.shoot_filter_size < 5)
			rune.shoot_filter_size = default_rune.shoot_filter_size;

        if (exposure_time < 50)
            exposure_time = 50;
        if (template_image_file.size() < 1)
            template_image_file = "template.bmp";
        if (small_template_image_file.size() < 1)
            small_template_image_file = "small_template.bmp";

        if(mode < 0)
            mode = 0;

        if(bullet_speed < 10)
            bullet_speed = 10;
        if(scale_z < 0.1)
            scale_z = 1.0;
        if(scale_z_480 < 0.1)
            scale_z_480 = 1.0;
	}

	void write(FileStorage& fs) const{
        // for debug image
        cvWriteComment(*fs, "\nFor Debug Image", 0);
        fs << "show_image" << show_image;
        fs << "save_result" << save_result;

		// for rune system
        cvWriteComment(*fs, "\nParameter for Rune System", 0);
		fs << "sudoku_cell_width" << rune.sudoku_cell_width
		   << "sudoku_cell_height" << rune.sudoku_cell_height
		   << "shoot_time_gap" << rune.shoot_time_gap
		   << "shoot_filter_size" << rune.shoot_filter_size;

		// for armor system
        cvWriteComment(*fs, "\nParameter for Armor Detection System", 0);
		fs << "min_light_gray" << armor.min_light_gray
			<< "min_light_height" << armor.min_light_height
			<< "avg_contrast_threshold" << armor.avg_contrast_threshold
			<< "light_slope_offset" << armor.light_slope_offset
			<< "max_light_delta_h" << armor.max_light_delta_h
			<< "min_light_delta_h" << armor.min_light_delta_h
			<< "max_light_delta_v" << armor.max_light_delta_v
			<< "max_light_delta_angle" << armor.max_light_delta_angle
			<< "avg_board_gray_threshold" << armor.avg_board_gray_threshold
			<< "avg_board_grad_threshold" << armor.avg_board_grad_threshold
			<< "grad_threshold" << armor.grad_threshold
			<< "br_threshold" << armor.br_threshold;

        // for enemy color
        cvWriteComment(*fs, "\nParameter for Enemy Color, 0(default) means for red, otherwise blue", 0);
        fs << "enemy_color" << armor.enemy_color;

        cvWriteComment(*fs, "\nMinimum / Maximun distance (cm) of detection", 0);
        fs << "min_detect_distance" << min_detect_distance;
        fs << "max_detect_distance" << max_detect_distance;

        // for armor template
        cvWriteComment(*fs, "\nParameter for Template", 0);
        fs << "template_image_file" << template_image_file;
        fs << "small_template_image_file" << std::string("small_template_image_file");

        // for camerar
        cvWriteComment(*fs, "\nParameter for Camera", 0);
        fs << "intrinsic_file_480" << intrinsic_file_480;
        fs << "intrinsic_file_720" << intrinsic_file_720;
        fs << "exposure_time" << exposure_time;

        // for system mode
        cvWriteComment(*fs, "\nParameter for Vision System Mode, 0(default) means for armor detection mode, 1 means for rune system mode", 0);
        fs << "mode" << mode;

        cvWriteComment(*fs, "\nBullet speed (m/s)", 0);
        fs << "bullet_speed" << bullet_speed;

        cvWriteComment(*fs, "\nScale factor of Z", 0);
        fs << "scale_z" << scale_z;
	}

public:
    int show_image;
    int save_result;
	RuneParam rune;
	ArmorParam armor;
    int mode;
    std::string intrinsic_file_480;
    std::string intrinsic_file_720;
    int exposure_time;
    std::string template_image_file;
    std::string small_template_image_file;
    double min_detect_distance;
    double max_detect_distance;
    double bullet_speed;
    double scale_z;
    double scale_z_480;
};

