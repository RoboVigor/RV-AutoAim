#include "HuaQToo.h"

using std::to_string;

int main()
{

    VideoCapture cap(0);
    Mat temp_mat1;
    cap >> temp_mat1;
    string datapath = "data/test0/img01.jpg";
    string *dd = &datapath;
    double time0 = 0.0;
    Image test(dd);
    while(1)
    {
        time0 = static_cast<double>(getTickCount());
        test.setSrcMat(temo_mat1);
        //test.setxmlpath(&xmlpath);
        test.refresh();
        test.reflect();
        test.getBest();
        test.getEuler();
        test.setPort();
        test.commute();
        test.showoff();
        if(waitKey(0) == 27) break;
        time0 = (static_cast<double>(getTickCount()) - time0) / getTickFrequency();
        cout << "time0: " << time0 << endl;
    }
    destroyAllWindows();
    return 0;
}
