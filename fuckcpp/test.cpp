#include "HuaQToo.h"

using std::to_string;

int main()
{
    /*
      Port testport;
      string path = "/dev/ttyTHS2";
      testport.setPath(&path);
      ui8 testnum[4] = { 0xff, 0xaa, 0xbb, 0xcc };
      testport.setAngle(testnum);
      int fd = testport.dakai();
      testport.xielu(fd);
      testport.showinf();
      close(fd);
    */
    //string xmlpath = "C://Users//hasee//Downloads//autoAim-master//what.xml";
    //createxml(&xmlpath);


    for(int i = 0; i < 7; i++)
    {
        string datapath = "data/test0/img0" + to_string(i + 1) + ".jpg";
        cout << datapath;
        string *dd = &datapath;
        Image test(dd);
        //test.setxmlpath(&xmlpath);
        test.refresh();
        test.reflect();
        test.getBest();
        test.getEuler();
        test.setPort();
        test.showoff();
        test.commute();
        if(waitKey(0) == 27) break;
    }
    destroyAllWindows();
    return 0;
}
