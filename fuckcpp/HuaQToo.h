#pragma once
//#include "stdafx.h"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <vector>
#include <fcntl.h>
#include <string>
#include <math.h>
#include <stdlib.h>
#include <queue>
#include <algorithm>
//#define vector<vector<Point>> ctype
#include <unistd.h>
#include <termios.h>
#include <sys/types.h>
#include <sys/stat.h>

typedef uint8_t ui8;
typedef uint16_t ui16;
typedef uint32_t ui32;
typedef uint64_t ui64;
typedef int16_t i16;
typedef int8_t i8;
typedef std::vector<cv::Point> cv_c;
typedef std::vector<cv_c> cv_ct;
typedef std::vector<cv_ct *> cv_cts;

using std::cout;
using std::endl;
using std::vector;
using std::queue;
using std::string;
using namespace cv;

union inf
{
    ui64 akb;
    ui8 list[8];
};

enum E_HuaQ
{
    X = 0, Y = 1, WIDTH = 3, HEIGHT = 2
};

class Lamp
{
public:
    cv_c counters;
    float greyscale;
    float error;
    Rect rect;
    float area;
    bool paired;

    Lamp() : greyscale(0), error(0), area(0), paired(false) {}
    Lamp(cv_c &r_counters, Rect &r_rect, float ggreyscale, float aarea, float tempsum);
    Lamp(Lamp &other);
    Lamp(const Lamp &other);
    Lamp &operator=(Lamp &other);
    ~Lamp() {}
    bool cmp(float other, int flag = 0)
    {
        if (0 == flag)
            return rect.x <= other ? true : false;//true==smaller
        else
            return rect.x > other ? true : false;//true==larger
    }
};

struct Parameters
{
    int area_region[2];
    float lamp_weights[2];
    float pair_weights[4];
    float pair_passline;
    float lamp_passline;
    float pairerror[3];
    Parameters();
    int readFxml(string *p_path);
    int writeTxml(string *p_path);
};

class lamps
{
public:
    Lamp left;
    Lamp right;
    lamps() {};
    lamps(Lamp &templeft, Lamp &tempright)
    {
        left = templeft;
        right = tempright;
    }
    lamps(lamps &other)
    {
        left = other.left;
        right = other.right;
    }
    lamps(const lamps &other)
    {
        left = const_cast<Lamp &>(other.left);
        right = const_cast<Lamp &>(other.right);
    }
    lamps &operator=(const lamps &other);
    lamps &operator=(lamps &other);
    ~lamps()
    {
    }
};

class ImageToolBox
{
private:
    string path;
    Mat srcimg;
    Mat g_img;
    Mat tempimg;
    Mat tempimg2;
    Mat dstimg;
    Mat p_img[3];
    int lampsize;

    cv_ct conterlist;
    vector<Rect> rectlist;
    vector<Lamp> lamplist;
    vector<lamps> pairlist;
    vector<int> pairdellist;

    cv_ct pc;
    int aarea;
    vector<float> error;
    vector<float> merror;
    float ftemp;

    void setIntial();
    vector<float> *getLampError(int greyscale, Rect rect);
    vector<float> *getPairError(Lamp &here, Lamp &other);
    void sortdel(int size);
public:
    int pairsize;
    Parameters para;
    ImageToolBox(string *ppath = nullptr);
    ImageToolBox(char *cpppath);
    ~ImageToolBox() {}
    void showoff();
    void showoff(int* loc);
    void setSrcMat(Mat &temp);
    Mat &preprocess(int ifpre = 1);
    Mat threshold(Mat &src_img);
    void findContours(Mat &src_img);
    vector<Lamp> *findlamps();
    void pairLamps();
    void sort();
    vector<lamps> &getpair()
    {
        return pairlist;
    }
};

class Port
{
private:
    string path;
    inf AKB48;
    inf *tp_AKB48;
    int readxml();
    int writexml();
public:
    enum class Port_loc : int
    {
        INT1, INT2, LEN, PITCH1, PITCH2, YAWN1, YAWN2, ENDC
        //ENDC, YAWN2, YAWN1, PITCH2, PITCH1, LEN, INT2, INT1
    };
    typedef Port_loc loc;
    Port();
    ~Port() {}
    int dakai(string *p_path = nullptr);
    int xielu(int fd = -1);
    int duqu(int fd = -1, size_t count = 0);
    int write2xml();
    int read2xml();
    void setPath(string *p_path);
    void setPath(char *p_path);
    void setAngle(loc which, ui8 num = 0);
    void setAngle(ui8 *p_num = nullptr);
    void showinf();
};

class Image : private ImageToolBox
{
private:
    int area;
    static constexpr int cy_image = 240;
    static constexpr int cx_image = 320;
    static constexpr float awidth = 125.0;
    static constexpr float aheight = 140.0;

    float centloc[2];
    string path;
    Port termio;
    Mat srcImage;
    Mat dstImage;
    string xmlpath;
    vector<lamps> pairlist;
    vector<float> depths;
    int depthsize;
    int  mindiff;
    int minpoint;
    float ratio;
    float euler_y;
    float euler_x;
    ui8 pitch1;
    ui8 pitch2;
    ui8 yawn1;
    ui8 yawn2;

    double temp;
    float cal_area(lamps &l_lamps);
public:
    Image(string *p_path = nullptr);
    int refresh();
    int reflect();
    int getEuler();
    void commute();
    void setSrcMat(Mat &temp);
    void setxmlpath(string *p_path)
    {
        xmlpath = *p_path;
    }
    int getBest();
    int setPort();
    void showoff();
    ~Image() {}
};

/****************************************************/
void ImageToolBox::sort()
{
    Lamp temp;
    for (int i = 0; i < lampsize - 1; ++i)
    {
        for (int j = i + 1; j < lampsize; ++j)
        {
            if (lamplist.at(i).rect.x > lamplist.at(j).rect.x)
            {
                temp = lamplist.at(i);
                lamplist.at(i) = lamplist.at(j);
                lamplist.at(j) = temp;
            }
        }
    }
}
/****************************************************/
//Lamp
Lamp::Lamp(cv_c &r_counters, Rect &r_rect, float ggreyscale, float aarea, float tempsum)
{
    counters = r_counters;
    rect = r_rect;
    greyscale = ggreyscale;
    area = aarea;
    error = tempsum;
    paired = false;
}

Lamp::Lamp(Lamp &other)
{
    counters = other.counters;
    greyscale = other.greyscale;
    error = other.error;
    rect = other.rect;
    area = other.area;
    paired = other.paired;
}

Lamp::Lamp(const Lamp &other)
{
    counters = other.counters;
    greyscale = other.greyscale;
    error = other.error;
    rect = other.rect;
    area = other.area;
    paired = other.paired;
}

Lamp &Lamp::operator=(Lamp &other)
{
    this->counters = other.counters;
    this->greyscale = other.greyscale;
    this->error = other.error;
    this->rect = other.rect;
    this->area = other.area;
    this->paired = other.paired;
    return *this;
}
/****************************************************/
lamps &lamps::operator=(lamps &other)
{
    this->left = other.left;
    this->right = other.right;
    return *this;
}

lamps &lamps::operator=(const lamps &other)
{
    this->left = const_cast<Lamp &>(other.left);
    this->right = const_cast<Lamp &>(other.right);
    return *this;
}

/****************************************************/
//parameter public class
Parameters::Parameters()
{
    area_region[0] = 32;
    area_region[1] = 3200;
    lamp_weights[0] = 1;
    lamp_weights[1] = 0.5;
    lamp_passline = 1.5;
    pair_passline = 2.5;
    pair_weights[0] = 2;
    pair_weights[1] = 1;
    pair_weights[2] = 3;
    pair_weights[3] = 2.5;
}

int Parameters::readFxml(string *p_path)
{
    FileStorage fs(p_path->c_str(), FileStorage::READ);
    if (!fs.isOpened())
    {
        fputs("cannot open fucker!\n", stderr);
        return 0;
    }
    fs["areaRegion0"] >> area_region[0];
    fs["areaRegion1"] >> area_region[1];
    fs["pair_weights0"] >> pair_weights[0];
    fs["pair_weights1"] >> pair_weights[1];
    fs["pair_weoghts2"] >> pair_weights[2];
    fs["pair_weights3"] >> pair_weights[3];
    fs["lamp_passline"] >> lamp_passline;
    fs["lamp_weights0"] >> lamp_weights[0];
    fs["lamp_weights1"] >> lamp_weights[1];
    fs["pair_passline"] >> pair_passline;
    fs.release();
    return 1;
}

int Parameters::writeTxml(string *p_path)
{
    FileStorage fs(p_path->c_str(), FileStorage::WRITE);
    if (!fs.isOpened())
    {
        fputs("cannot open fucker!\n", stderr);
        return 0;
    }
    fs << "areaRegion0" << area_region[0];
    fs << "areaRegion1" << area_region[1];
    fs << "pair_weights0" << pair_weights[0];
    fs << "pair_weights1" << pair_weights[1];
    fs << "pair_wrights2" << pair_weights[2];
    fs << "pair_weights3" << pair_weights[3];
    fs << "lamp_passline" << lamp_passline;
    fs << "lamp_weights0" << lamp_weights[0];
    fs << "lamp_weights1" << lamp_weights[1];
    fs << "pair_passline" << pair_passline;
    fs.release();
    return 1;
}
/****************************************************/
//Image tool box
void ImageToolBox::setIntial()
{
    aarea = 0;
    ftemp = 0;
    lampsize = 0;
    pairsize = 0;
}

ImageToolBox::ImageToolBox(string *ppath)
{
    path = *ppath;
    srcimg = imread(path);
    setIntial();
}

ImageToolBox::ImageToolBox(char *cppath)
{
    path = *cppath;
    srcimg = imread(path);
    setIntial();
}
void ImageToolBox::showoff()
{
    //imshow("srcimg", srcimg);
    //imshow("dstimg", dstimg);
    lamps temp;
    for (int i = 0; i < pairsize; ++i)
    {
        temp.left = pairlist.at(i).left;
        temp.right = pairlist.at(i).right;
        //cout << "left" << pairlist.at(i).left.rect.x << " "<<pairlist.at(i).left.rect.y << endl;
        //cout << "right" << pairlist.at(i).right.rect.x << " " << pairlist.at(i).right.rect.y << endl;
        //rectangle(srcimg,temp.right.rect, Scalar(0, 255, 0), 3, 1);
        //rectangle(srcimg, temp.left.rect, Scalar(0, 255, 0), 3, 1);
        rectangle(srcimg, Rect(temp.left.rect.x, temp.left.rect.y, (temp.right.rect.x - temp.left.rect.x + temp.left.rect.width), (temp.right.rect.y - temp.left.rect.y + temp.right.rect.height)), Scalar(0, 108, 239), 3, 1);
    }
    for (int i = 0; i < lamplist.size(); ++i)
    {
        temp.left = lamplist.at(i);
        temp.right = lamplist.at(i);
        //cout << "left" << lamplist.at(i).left.rect.x << " " << pairlist.at(i).left.rect.y << endl;
        //cout << "right" << pairlist.at(i).right.rect.x << " " << pairlist.at(i).right.rect.y << endl;
        //rectangle(srcimg, temp.right.rect, Scalar(0, 0, 255), 1, 1);
        //rectangle(srcimg, temp.left.rect, Scalar(0, 0, 255), 1, 1);
        //rectangle(srcimg, Rect(temp.left.rect.x, temp.left.rect.y, (temp.right.rect.width + temp.right.rect.x), (temp.left.rect.height)), Scalar(0, 0, 255), 1, 1);
    }
    imshow("rectimg", srcimg);
}


void ImageToolBox::showoff(int* loc)
{   // au
    line(srcimg, Point(loc[0] - 5, loc[1]), Point(loc[0] + 5, loc[1]), Scalar(251, 64, 224), 2);
    line(srcimg, Point(loc[0], loc[1] - 5), Point(loc[0], loc[1] + 5), Scalar(251, 64, 224), 2);
    line(srcimg, Point(loc[2] - 5, loc[3]), Point(loc[2] + 5, loc[3]), Scalar(129, 64, 255), 2);
    line(srcimg, Point(loc[2], loc[3] - 5), Point(loc[2], loc[3] + 5), Scalar(129, 64, 255), 2);
    showoff();
}

Mat &ImageToolBox::preprocess(int ifpre)
{
    split(srcimg, p_img);
    g_img = p_img[1];
    if (1 == ifpre)
    {
        Size ksize = { 3, 3 };
        GaussianBlur(g_img, tempimg, ksize, 0, 0, BORDER_DEFAULT);
        medianBlur(tempimg, tempimg, 5);
        Sobel(tempimg, tempimg, CV_8U, 1, 0);
        cv::threshold(tempimg, tempimg, 250, 255, THRESH_BINARY);
        Mat element1 = getStructuringElement(MORPH_RECT, Size(9, 1));//9,1
        Mat element2 = getStructuringElement(MORPH_RECT, Size(8, 5));//8,2
        dilate(tempimg, tempimg, element2);
        erode(tempimg, tempimg2, element1);
        dilate(tempimg2, dstimg, element2);
        //cv::threshold(g_img, dstimg, 180, 255, THRESH_BINARY);

        return dstimg;
    }
    return g_img;
}

Mat ImageToolBox::threshold(Mat &src_img)
{
    double ret = cv::threshold(src_img, tempimg, 0, 255, THRESH_BINARY + THRESH_OTSU);
    cv::threshold(src_img, tempimg, (255 - ret) * 0.5 + ret, 255, THRESH_BINARY);
    return tempimg;
}

void ImageToolBox::findContours(Mat &src_img)
{

    //vector<Vec4i> hi;
    Mat temp = src_img.clone();
    //imshow("w", dstimg);
    cv::findContours(temp, pc, CV_RETR_TREE, CV_CHAIN_APPROX_SIMPLE);

    //vector<vector<vector<Point>>> contlist;
    //vector<Rect> rectlist;
    Rect temprect;
    //drawContours(srcimg, pc, -1, Scalar(255, 0, 0), 3);

    for (int i = 0; i < pc.size(); ++i)
    {
        temprect = boundingRect(pc.at(i));
        aarea = temprect.width * temprect.height;
        if (aarea > para.area_region[0] && aarea < para.area_region[1])
        {
            conterlist.push_back(pc.at(i));
            rectlist.push_back(temprect);
        }
    }
}

vector<float> *ImageToolBox::getLampError(int greyscale, Rect rect)
{
    merror.clear();
    ftemp = max(0.0, (255.0 - (float)greyscale) / 85.0 - 1.0);
    merror.push_back(ftemp);
    ftemp = max((double)0.0, (2.5 - (float)rect.height / (float)rect.width) / 2.5);
    merror.push_back(ftemp);
    //cout << "greyscale: " << greyscale << endl;
    //cout << "width/height: " << (float)rect.height / (float)rect.width << endl;
    return &merror;
}

vector<Lamp> *ImageToolBox::findlamps()
{
    vector<float> area;
    Mat roi;
    vector<Scalar> meangrey;
    float tempsum = 0;
    for (int i = 0; i < conterlist.size(); ++i)
    {
        area.push_back(contourArea(conterlist.at(i)));
        //cout << "area: " << area.at(i) << endl;
        //Moments mom = moments(conterlist[i]);
        roi = g_img(Rect(rectlist.at(i)));
        meangrey.push_back(mean(roi));
    }
    //vector<float> merror;
    vector<float> *p_merror;
    for (int i = 0; i < rectlist.size(); ++i)
    {
        p_merror = getLampError(meangrey[i][0], rectlist.at(i));
        tempsum = 0;
        for (int j = 0; j < 2; ++j)
        {
            //cout << "p_merror->at(j)"<< p_merror->at(j)<<endl;
            tempsum += p_merror->at(j) * para.lamp_weights[j];
            //cout << "tempsum " << tempsum<<endl;
        }
        if (tempsum < para.lamp_passline)
        {
            Lamp templamp(conterlist.at(i), rectlist[i], meangrey[i][0], area[i], tempsum);
            lamplist.push_back(templamp);
        }
    }
    lampsize = lamplist.size();
    //cout << conterlist.size() << ' ' << rectlist.size() << endl;
    //cout << lampsize << endl;
    sort();
    //for (int i = 0; i < lampsize; ++i)
    //cout << "lamp " << i << " " << lamplist.at(i).rect.x<<" "<<lamplist.at(i).rect.y<<endl;
    return &lamplist;
}

vector<float> *ImageToolBox::getPairError(Lamp &here, Lamp &other)
{
    error.clear();
    ftemp = max(0.0, abs((here.rect.y - other.rect.y)) / here.rect.height - 0.1);
    error.push_back(ftemp);
    ftemp = abs((here.area - other.area) / here.area);
    error.push_back(ftemp);
    int row_begin = (int)((here.rect.y + other.rect.y) / 2);
    int row_stop = (int)((here.rect.y + here.rect.height + other.rect.y + other.rect.height) / 2);
    int diff = row_stop - row_begin;
    int col_center = (here.rect.x + here.rect.width + other.rect.x) / 2;
    int col_begin = (int)(col_center - diff / 2);
    int col_end = col_begin + diff;
    Mat roi = g_img(Rect(col_begin, row_begin, diff, diff));
    if (0 == roi.size)
    {
        error.push_back(1);
    }
    else
    {
        ftemp = mean(roi)[0];
        ftemp = max((float)0.0, ((140 - ftemp) / 140));
        error.push_back(ftemp);
    }
    if (here.rect.y >= other.rect.y)
    {
        ftemp = ((float)other.rect.x + (float)other.rect.width - (float)here.rect.x) / ((float)here.rect.y + (float)here.rect.height - (float)other.rect.y + 0.1);
        //cout << "ftemp: "<<ftemp;
    }
    else
    {
        ftemp = (float)((other.rect.x + other.rect.width - here.rect.x)) / (float)((other.rect.y + other.rect.height - here.rect.y + 0.1));
        //cout << "ftemp: "<<ftemp;
    }
    if (ftemp > 3.5 || ftemp < 1.2)
        error.push_back(1);
    else
        error.push_back(0);
    /*
    cout << "error: ";
    for (int i = 0; i < 4; ++i)
    {
    cout << error.at(i)<<" ";
    }
    cout << endl;*/
    return &error;
}

void ImageToolBox::setSrcMat(Mat &temp)
{
    srcimg = temp;
}
void ImageToolBox::sortdel(int size)
{
    int temp = 0;
    for (int i = 0; i < size - 1; ++i)
    {
        for (int j = i + 1; j < size; ++j)
        {
            if (pairdellist.at(i) < pairdellist.at(j))
            {
                temp = pairdellist.at(i);
                pairdellist.at(i) = pairdellist.at(j);
                pairdellist.at(j) = temp;
            }
        }
    }
}

void ImageToolBox::pairLamps()
{
    Lamp pair_left;
    Lamp pair_right;
    Lamp _pair_right;
    bool isPaired = false;
    float _error = 0;
    float error = 0;
    vector<float> *p_merror = nullptr;
    //Lamp pair[2];
    //cout << "lampsize: " << lampsize << endl;
    for (int i = 0; i < lampsize - 1; ++i)
    {
        pair_left = lamplist.at(i);
        //cout << "left x: " << pair_left.rect.x << endl;
        isPaired = false;
        if (!pair_left.paired)
        {
            error = para.pair_passline;
            int _j = 0;
            for (int j = i + 1; j < lampsize; ++j)
            {
                _error = 0;
                _pair_right = lamplist.at(j);
                p_merror = getPairError(pair_left, _pair_right);
                for (int z = 0; z < 4; ++z)
                {
                    _error += p_merror->at(z) * para.pair_weights[z];
                }
                //cout << "_error" << _error << endl;
                if (_error < error)
                {
                    error = _error;
                    pair_right = _pair_right;
                    isPaired = true;
                    _j = j;
                    //cout << "--------------------" << endl;
                    //cout << pair_left.area << " " << pair_right.area << " "<< pair_left.rect.height << endl;
                    //cout << p_merror->at(0) << " " << p_merror->at(1) << " " << p_merror->at(2) << " " << p_merror->at(3);
                    //cout << "error: " << error << endl;
                }
            }
            if (isPaired)
            {
                pair_left.paired = true;
                pair_right.paired = true;
                lamplist.at(_j).paired = true;
                lamplist.at(i).paired = true;
                lamps temp(pair_left, pair_right);
                pairlist.push_back(temp);
                //vector<Lamp> temp;
                //temp.push_back(pair_left);
                //temp.push_back(pair_right);
                //pairllist.push_back(temp);
            }
        }
    }
    pairsize = pairlist.size();
    //for (int i = 0; i < pairsize; ++i)
    //{
    //  cout << "pairleft " << i << " " << pairlist.at(i).left.rect.x << ' '<<pairlist.at(i).left.rect.y << endl;
    //  cout << "pairright " << i << " " << pairlist.at(i).right.rect.x << ' '<<pairlist.at(i).right.rect.y << endl;
    //}
    for (int i = 0; i < pairsize - 1; ++i)
    {
        if (i == pairsize - 1)
            break;
        for (int j = i + 1; j < pairsize; ++j)
        {
            if ((pairlist.at(i).left.rect.x) <= (pairlist.at(j).left.rect.x)
                    && (pairlist.at(i).right.rect.x) <= (pairlist.at(j).right.rect.x)
                    && abs((pairlist.at(j).left.rect.y) - (pairlist.at(i).left.rect.y)) < 25)
            {

                pairdellist.push_back(i);
                break;
            }
        }
    }
    cout << "pairsize: " << pairsize << endl;
    vector<lamps>::iterator it = pairlist.begin();
    int delsize = pairdellist.size();
    cout << "del size " << delsize << endl;
    int countdel = 0;
    int countpair = 0;
    sortdel(delsize);
    //cout << "del num "<<endl;
    for (int i = 0; i < delsize; ++i)
    {
        cout << pairdellist.at(i) << ' ';
    }
    for (countdel = 0; countdel < delsize; ++countdel)
    {
        countpair = pairdellist.at(countdel) - countdel;
        pairlist.erase(pairlist.begin() + countpair);
    }
    pairsize = pairlist.size();
}

/****************************************************/
//Port class

Port::Port()
{
    AKB48.list[(int)loc::INT1] = 0xAB;
    AKB48.list[(int)loc::INT2] = 0xCD;
    AKB48.list[(int)loc::LEN] = 0xfa;
    for (int i = (int)loc::PITCH1; i <= (int)loc::YAWN2; ++i)
    {
        AKB48.list[i] = 0x00;
    }
    AKB48.list[(int)loc::ENDC] = 0xff;
    tp_AKB48 = nullptr;
}

int Port::dakai(string *p_path)
{
    if (nullptr != p_path)
        path = *p_path;
    struct termios options;
    int fd = -1;
    fd = open(path.c_str(), O_RDWR | O_NOCTTY | O_NDELAY);
    if (-1 == fd)
    {
        perror("open port failed.\n");
    }
    else
    {
        //fcntl(fd, F_SETFL, 0);
        tcgetattr(fd, &options);
        bzero(&options, sizeof(options));
        options.c_cflag |= B9600 | CLOCAL | CREAD; // 设置波特率，本地连接，接收使能
        options.c_cflag &= ~CSIZE;                     // 屏蔽数据位
        options.c_cflag |= CS8;                    // 数据位为 8 ，CS7 for 7
        options.c_cflag &= ~CSTOPB;                // 一位停止位， 两位停止为 |= CSTOPB
        options.c_cflag |= PARENB;                  // 有校验
        options.c_cflag &= ~PARODD;                // 偶校验
        tcflush(fd, TCIOFLUSH);
        if (tcsetattr(fd, TCSANOW, &options) != 0)     // TCSANOW立刻对值进行修改
            return  false;
        /*opt.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
        opt.c_oflag &= ~OPOST;
        cfsetispeed(&opt, B115200);
        cfsetospeed(&opt, B115200);
        tcsetattr(fd,TCSANOW, &opt);
        tcflush(fd, TCIOFLUSH);*/
    }
    return fd;
}

int Port::xielu(int fd)
{
    if (-1 == fd)
        return 0;
    int if_suc = write(fd, &AKB48.akb, sizeof(AKB48.akb));
    //char hahaha[2] = "h";
    //int if_suc = write(fd, hahaha, sizeof(hahaha));
    if (if_suc < 0)
    {
        fputs("fuckyou, write wrong\n", stderr);
        return 0;
    }
    return 1;
}

int Port::duqu(int fd, size_t count)
{
    if (-1 == fd)
        return 0;
    fcntl(fd, F_SETFL, FNDELAY);
    read(fd, tp_AKB48, count);
}

int Port::writexml()
{
    //openXmlFS
    FileStorage fs(path.c_str(), FileStorage::WRITE);
    if (!fs.isOpened())
    {
        fputs("can not open xml!\n", stderr);
        return 0;
    }
    fs << "Pitch1" << AKB48.list[(int)loc::PITCH1];
    fs << "Pitch2" << AKB48.list[(int)loc::PITCH2];
    fs << "Yawn1" << AKB48.list[(int)loc::YAWN1];
    fs << "Yawn2" << AKB48.list[(int)loc::YAWN2];
    fs.release();
    return 1;
}

int Port::write2xml()
{
    int temp = writexml();
    return temp;
}

int Port::readxml()
{
    FileStorage fs(path.c_str(), FileStorage::READ);
    if (!fs.isOpened())
    {
        fputs("can not open xml!\n", stderr);
        return 0;
    }
    fs["Pitch1"] >> AKB48.list[(int)loc::PITCH1];
    fs["Pitch2"] >> AKB48.list[(int)loc::PITCH2];
    fs["Yawn1"] >> AKB48.list[(int)loc::YAWN1];
    fs["Yawn2"] >> AKB48.list[(int)loc::YAWN2];
    fs.release();
    return 1;
}

int Port::read2xml()
{
    int temp = readxml();
    return temp;
}

void Port::setPath(string *p_path)
{
    path = *p_path;
}

void Port::setPath(char *p_path)
{
    path = *p_path;
}

void Port::setAngle(loc which, ui8 num)
{
    AKB48.list[(int)which] = num;
}

void Port::setAngle(ui8 *num)
{
    if (sizeof(num) < 4)
        fputs("number doesnot enough.\n", stderr);
    for (int i = (int)loc::PITCH1; i <= (int)loc::YAWN2; ++i)
    {
        AKB48.list[i] = num[i - 3];
        //cout << "wtf??? " << (i - 3);
    }
}

void Port::showinf()
{
    //%I64x
    printf("%llx\n", AKB48.akb);
    for (int i = 0; i <= 7; ++i)
    {
        printf("%02x ", AKB48.list[i]);
    }
    //std::cin.get();
}

/*int main() {
inf test;
for (int i = 0; i < 6; ++i)
{
test.list[i] = 0x01;
printf("%x ",test.list[i]);
}
cout << endl;
printf("%x", test.akb);
std::cin.get();
return 0;
}*/

/**************************************************/
//Image class
Image::Image(string *p_path) : ImageToolBox(p_path)
{
    //ImageToolBox::ImageToolBox(p_path);
    area = 0;
    centloc[X] = 320;
    centloc[Y] = 240;
}

void Image::setSrcMat(Mat &temp)
{
    ImageToolBox::setSrcMat(temp);
}

int Image::refresh()
{
    //ImageToolBox::para.readFxml(&xmlpath);
    dstImage = ImageToolBox::preprocess();
    //imshow("dstImage", dstImage);
    ImageToolBox::findContours(dstImage);
    ImageToolBox::findlamps();
    ImageToolBox::pairLamps();
    pairlist = ImageToolBox::getpair();
    return 1;
}

float Image::cal_area(lamps &l_lamps)
{
    int leftx = l_lamps.left.rect.x + l_lamps.left.rect.width;
    int width = l_lamps.left.rect.height > l_lamps.right.rect.height ? l_lamps.left.rect.height : l_lamps.right.rect.height;
    int rightx = l_lamps.right.rect.x;
    return abs((rightx - leftx)) * width;
}

int Image::reflect()
{
    depths.clear();
    for (int i = 0; i < ImageToolBox::pairsize; ++i)
    {
        area = cal_area(pairlist.at(i));
        //cout << "area "<<area << endl;
        temp = (1.0 / area);
        temp = pow(temp, 0.627);
        temp = 106.5 * temp * 1000;
        cout << "temp " << temp << endl;
        depths.push_back(temp);

        //if (i!=0)
        //{
        //  if (temp < mindepth)
        //      mindepth = temp;
        //  return mindepth;
        //}
        //mindepth = temp;
        //return mindepth;
    }
    depthsize = depths.size();
    cout << "depthsize" << depthsize << endl;
    return 1;
}

int Image::getBest()
{
    if (depthsize < 1)
    {
        minpoint = -1;
        return -1;
    }
    else if (1 == depthsize)
    {
        minpoint = 0;
        int i = 0;
        centloc[X] = (
                         pairlist.at(i).left.rect.x
                         + pairlist.at(i).left.rect.width
                         + pairlist.at(i).right.rect.x
                     ) / 2.0;
        centloc[Y] = (
                         pairlist.at(i).left.rect.y * 2
                         + pairlist.at(i).left.rect.height
                         + pairlist.at(i).right.rect.y * 2
                         + pairlist.at(i).right.rect.height
                     ) / 4.0;
        return 1;
    }
    else
    {
        minpoint = -1;
        for (int i = 0; i < depthsize; ++i)
        {
            centloc[X] = (
                             pairlist.at(i).left.rect.x
                             + pairlist.at(i).left.rect.width
                             + pairlist.at(i).right.rect.x
                         ) / 2.0;
            centloc[Y] = (
                             pairlist.at(i).left.rect.y * 2
                             + pairlist.at(i).left.rect.height
                             + pairlist.at(i).right.rect.y * 2
                             + pairlist.at(i).right.rect.height
                         ) / 4.0;
            temp = fabs(centloc[X] - cx_image);
            temp = temp * temp;
            temp += fabs(centloc[Y] - cy_image) * fabs(centloc[Y] - cy_image);
            if (i != 0)
            {
                if (mindiff > temp)
                {
                    mindiff = temp;
                    minpoint = i;
                }
            }
            else
            {
                mindiff = temp;
                minpoint = i;
            }
        }
        return minpoint;
    }
}

int Image::getEuler()
{
    int tempdeth = depths.at(minpoint);
    ratio = awidth / (pairlist.at(minpoint).right.rect.x - pairlist.at(minpoint).left.rect.x + pairlist.at(minpoint).left.rect.width);
    ratio += aheight / (pairlist.at(minpoint).right.rect.y - pairlist.at(minpoint).left.rect.y + pairlist.at(minpoint).left.rect.height);
    ratio = ratio / 2.0;
    temp = (centloc[Y] - cy_image) * ratio;
    euler_y = (asin(temp / depths.at(minpoint)) * 180.0 / 3.14159297) / 100.0;
    temp = (centloc[X] - cx_image) * ratio;
    euler_x = (asin(temp / depths.at(minpoint)) * 180.0 / 3.14159297) / 100.0;
    cout << "!!" << euler_x << " " << euler_y << endl;
    return 1;
}

int Image::setPort()
{
    i16 temp1 = euler_y * 10000;
    //cout <<"euler_y "<< euler_y << endl;
    i16 temp2 = euler_x * 10000;
    i16 temp3 = 0;
    if (temp2 >  32767)
    {
        temp2 = 32767;
    }
    else if (temp2 < -32768)
    {
        temp2 = -32768;
    }
    else
    {
        temp3 = temp2 & 0x00ff;
        //printf("temp3: %0x", temp3);
        yawn2 = temp3;
        //printf("yawn2: %0x\n", yawn2);
        temp3 = temp2 & 0xff00;
        yawn1 = temp3 >> 8;
        //printf("yawn1: %0x\n", yawn1);
    }
    if (temp1 >  32767)
    {
        temp1 = 32767;
    }
    else if (temp1 < -32768)
    {
        temp1 = -32768;
    }
    else
    {
        temp3 = temp1 & 0x00ff;
        //printf("temp3: %0x", temp3);
        pitch2 = temp1;
        //printf("yawn2: %0x\n", yawn2);
        temp3 = temp1 & 0xff00;
        pitch1 = temp1 >> 8;
        //printf("yawn1: %0x\n", yawn1);
    }
    //printf("mindiff: %0x\n", temp2);
    //pitch2,pitch1,yawn2,yawn1;
    //termio.setAngular(*)
    ui8 angle[4];
    angle[0] = pitch1;
    angle[1] = pitch2;
    angle[2] = yawn1;
    angle[3] = yawn2;

    termio.setAngle(angle);
    return 1;
}

void Image::commute()
{
    string path = "/dev/ttyTHS2";
    termio.setPath(&path);
    int fd = termio.dakai();
    termio.xielu(fd);
    termio.showinf();
    close(fd);
}

void Image::showoff()
{
    cout << "mindiffsize " << sizeof(mindiff) << endl;
    cout << "minpoint: " << minpoint << endl;
    cout << "centloc_x: " << centloc[X] << endl;
    cout << "centloc_y" << centloc[Y] << endl;
    cout << "euler_x: " << euler_x << endl;
    cout << "euler_y: " << euler_y << endl;
    int temploc[4];
    temploc[0] = centloc[X];
    temploc[1] = centloc[Y];
    temploc[2] = cx_image;
    temploc[3] = cy_image;
    ImageToolBox::showoff(temploc);
}