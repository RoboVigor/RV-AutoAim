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

#include "opencv2/highgui/highgui.hpp"
#include "AngleSolver.hpp"

#define TRUNC_ABS(a) ((a) > 0 ? (a) : 0);
#define POINT_DIST(p1,p2) std::sqrt((p1.x-p2.x)*(p1.x-p2.x) + (p1.y-p2.y)*(p1.y-p2.y))

enum EnemyColor { RED = 0, BLUE = 1};

struct ArmorParam {
	uchar min_light_gray;	        // 板灯最小灰度值
	uchar min_light_height;			// 板灯最小高度值
	uchar avg_contrast_threshold;	// 对比度检测中平均灰度差阈值，大于该阈值则为显著点
	uchar light_slope_offset;		// 允许灯柱偏离垂直线的最大偏移量，单位度
    int  max_light_delta_h;         // 左右灯柱在水平位置上的最大差值，像素单位
	uchar min_light_delta_h;		// 左右灯柱在水平位置上的最小差值，像素单位
	uchar max_light_delta_v;		// 左右灯柱在垂直位置上的最大差值，像素单位
	uchar max_light_delta_angle;	// 左右灯柱在斜率最大差值，单位度
	uchar avg_board_gray_threshold; // 矩形区域平均灰度阈值，小于该阈值则选择梯度最小的矩阵
	uchar avg_board_grad_threshold; // 矩形区域平均梯度阈值，小于该阈值则选择梯度最小的矩阵
    uchar grad_threshold;			// 矩形区域梯度阈值，在多个矩形区域中选择大于该阈值像素个数最少的区域  (not used)
	uchar br_threshold;				// 红蓝通道相减后的阈值
    uchar enemy_color;                 // 0 for red, otherwise blue

    ArmorParam(){
        min_light_gray = 210;
		min_light_height = 8;
        avg_contrast_threshold = 110;
		light_slope_offset = 30;
        max_light_delta_h = 450;
		min_light_delta_h = 12;
		max_light_delta_v = 50;
		max_light_delta_angle = 30;
        avg_board_gray_threshold = 80;
        avg_board_grad_threshold = 25;
        grad_threshold = 25;
		br_threshold = 30;
        enemy_color = 0;
	}
};

class ArmorDetector {
public:
    ArmorDetector(const ArmorParam & para = ArmorParam()){
        pitch_angle = 0;
        s_solver = NULL;
        l_solver = NULL;
        _para = para;
        _res_last = cv::RotatedRect();
        _dect_rect = cv::Rect();
        _is_small_armor = false;
        _lost_cnt = 0;
        _is_lost = true;
	}
    void setPara(const ArmorParam & para){
        _para = para;
    }

    void setPnPSlover(AngleSolver * solver_s, AngleSolver * solver_l){
        s_solver = solver_s;
        l_solver = solver_l;
    }

    void setPitchAngle(double angle){
        pitch_angle = angle;
    }

    void reset(){
        _res_last = cv::RotatedRect();
        _dect_rect = cv::Rect();
        _is_small_armor = false;
        _lost_cnt = 0;
        _is_lost = true;
    }

    bool isSamllArmor(){
        return _is_small_armor;
    }

    void initTemplate(const cv::Mat & _template, const cv::Mat & _template_small);
    cv::RotatedRect getTargetAera(const cv::Mat & src);
    void setLastResult(const cv::RotatedRect & rect){
        _res_last = rect;
    }
    const cv::RotatedRect & getLastResult() const{
        return _res_last;
    }

private:
    /**
     * @brief setImage Pocess the input (set the green component and sub of blue and red component)
     * @param src
     */
    void setImage(const cv::Mat & src);

    /**
     * @brief templateDist Compute distance between template and input image
     * @param img input image
     * @param is_smarect_pnp_solverll true if input image is a samll armor, otherwise, false
     * @return distance
     */
    int templateDist(const cv::Mat & img, bool is_small);

    /**
     * @brief findContourInEnemyColor Find contour in _max_color
     * @param left output left contour image (probably left lamp of armor)
     * @param right output righe edge (probably right lamp of armor)
     * @param contours_left output left contour
     * @param contours_right output right contour
     */
    void findContourInEnemyColor(
        cv::Mat & left, cv::Mat & right,
        std::vector<std::vector<cv::Point2i> > &contours_left,
        std::vector<std::vector<cv::Point2i> > &contours_right);

    /**
     * @brief findTargetInContours Find target rectangles
     * @param contours_left input left contour
     * @param contours_right input right contour
     * @param rects target rectangles (contains wrong area)
     */
    void findTargetInContours(
        const std::vector<std::vector<cv::Point> > & contours_left,
        const std::vector<std::vector<cv::Point> > & contours_right,
        std::vector<cv::RotatedRect> & rects,
        std::vector<double> & score);

    /**
     * @brief chooseTarget Choose the most possible rectangle among all the rectangles
     * @param rects candidate rectangles
     * @return the most likely armor (RotatedRect() returned if no proper one)
     */
    cv::RotatedRect chooseTarget(const std::vector<cv::RotatedRect> & rects, const std::vector<double> & score);

    /**
     * @brief boundingRRect Bounding of two ratate rectangle (minumum area that contacts two inputs)
     * @param left left RotatedRect
     * @param right right RotatedRect
     * @return minumum area that contacts two inputs
     */
    cv::RotatedRect boundingRRect(const cv::RotatedRect & left, const cv::RotatedRect & right);

    /**
     * @brief adjustRRect Adjust input angle
     * @param rect input
     * @return adjusted rotate rectangle
     */
    cv::RotatedRect adjustRRect(const cv::RotatedRect & rect);
    bool makeRectSafe(cv::Rect & rect, cv::Size size){
        if (rect.x < 0)
            rect.x = 0;
        if (rect.x + rect.width > size.width)
            rect.width = size.width - rect.x;
        if (rect.y < 0)
            rect.y = 0;
        if (rect.y + rect.height > size.height)
            rect.height = size.height - rect.y;
        if (rect.width <= 0 || rect.height <= 0)
            return false;
        return true;
    }

    bool broadenRect(cv::Rect & rect, int width_added, int height_added, cv::Size size){
        rect.x -= width_added;
        rect.width += width_added * 2;
        rect.y -= height_added;
        rect.height += height_added * 2;
        return makeRectSafe(rect, size);
    }

private:
    AngleSolver * s_solver;
    AngleSolver * l_solver;
    double pitch_angle;
    bool _is_lost;
    int _lost_cnt;
    bool _is_small_armor;           // true if armor is the small one, otherwise false
    cv::RotatedRect _res_last;      // last detect result
    cv::Rect _dect_rect;            // detect roi of original image
    ArmorParam _para;               // parameter of alg
    cv::Mat _binary_template;       // armor template binary image
    cv::Mat _binary_template_small; // small armor template binay image
    cv::Mat _src;                   // source image
    cv::Mat _g;                     // green component of source image
    cv::Mat _ec;                    // enemy color
    cv::Mat _max_color;             // binary image of sub between blue and red component
    cv::Size _size;
//    cv::Mat _gray;
//    cv::Mat _b;
//    cv::Mat _r;
};

