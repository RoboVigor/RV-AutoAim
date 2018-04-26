import cv2
import numpy
import io

class LOC():
    def __init__(self):
        self.X=0
        self.Y=1
        self.WIDTH=2
        self.HEIGHT=3

s_height_weight=2.55
s_width_weight=2.75

class AimImageToolBox():
    def __init__(self,src_img):
        if isinstance(src_img,str):
            self.srcimg=cv2.imread(src_img)
        elif isinstance(src_img,numpy.ndarray):
            self.srcimg=src_img
        else:
            print('not a opencv pic,fucker!!')
        self.sizes=self.srcimg.shape
        self.src_b,self.src_g,self.src_r=cv2.split(src_img)
        self.pplist=[]
        self.pppair=[]//self.pairs
        self.loc=LOC()

    def preprocess(self):
        self.dstimg=cv2.GaussianBlur(self.src_g, (3, 3), 0, 0, cv2.BORDER_DEFAULT)
        self.dstimg=cv2.medianBlur(self.dstimg, 5)
        self.dstimg = cv2.Sobel(self.dstimg, cv2.CV_8U, 1, 0,  ksize = 3)
        ret3, self.dstimg = cv2.threshold(self.dstimg, 250, 255, cv2.THRESH_BINARY)
        element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 6))
        self.dstimg= cv2.dilate(self.dstimg, element2, iterations = 1)
        self.dstimg = cv2.erode(self.dstimg, element1, iterations = 1)
        self.dstimg = cv2.dilate(self.dstimg, element2,iterations = 1)

    def filter(self):
        dst,counters,hir=cv2.findContours(self.dstimg,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for i in range(0,len(counters)):
            rect=cv2.minAreaRect(counters[i])
            x,y=rect[0]
            width,height=rect[1]
            if width<height:
                x=x-0.5*width
                y=y-0.5*height
                #print(x,y)
                self.pplist.append((x,y,width,height))
                #cv2.rectangle(self.srcimg,(int(x),int(y)),(int((x+width)),int((y+height))),(0,255,0),1,8)
            else:
                x=x-0.5*height
                y=y-0.5*width
                #print(x,y)
                self.pplist.append((x,y,height,width))
                #cv2.rectangle(self.srcimg,(int(x),int(y)),(int((x+height)),int((y+width))),(0,255,0),1,8)
        self.pplist.sort(key=lambda y_size:y_size[self.loc.Y],reverse=True)
        for i in range(0,len(self.pplist)-1):
            for j in range(i+1,len(self.pplist)):
                if self.pplist[i][self.loc.HEIGHT]>=self.pplist[j][self.loc.HEIGHT]:
                    s_height=self.pplist[j][self.loc.HEIGHT]
                else:
                    s_height=self.pplist[i][self.loc.HEIGHT]
                if abs(self.pplist[i][self.loc.HEIGHT]-self.pplist[j][self.loc.HEIGHT])<0.5*s_height:
                    if self.pplist[i][self.loc.Y]-self.pplist[j][self.loc.Y]<=s_height*0.43:
                        if abs(self.pplist[i][self.loc.X]-self.pplist[j][self.loc.X])<=(s_height*s_height_weight):
                            if self.pplist[i][self.loc.WIDTH]>self.pplist[j][self.loc.WIDTH]:
                                s_width=self.pplist[i][self.loc.WIDTH]
                            else:
                                s_width=self.pplist[j][self.loc.WIDTH]
                            if abs(self.pplist[i][0]-self.pplist[j][0])>s_width*s_width_weight:
                                self.pppair.append((self.pplist[i],self.pplist[j]))

    def showoff(self):
        print(self.pppair)
        for i in range(0,len(self.pppair)):
            x1=int(self.pppair[i][0][0])
            x2=int(self.pppair[i][1][0])
            y1=int(self.pppair[i][0][1])
            y2=int(self.pppair[i][1][1])
            height1=int(self.pppair[i][0][3])
            height2=int(self.pppair[i][1][3])
            width1=int(self.pppair[i][0][2])
            width2=int(self.pppair[i][1][2])
            cv2.rectangle(self.srcimg,(x1,y1),(x1+width1,y1+height1),(0,0,255),1,8)
            cv2.rectangle(self.srcimg,(x2,y2),(x2+width2,y2+height2),(255,0,0),1,8)
        cv2.imshow('dst',self.srcimg)
    
    def setfilter(self,shw,shh):
        self.s_height_weight=shh
        self.s_width_weight=shw
    
    def get(self,index=all):
        return self.pppair[index]

    def getlen(self):
        return len(self.pppair)
    
    def area(self,index=0):
        a_height=self.pppair[index][0][self.loc.Y]-self.pppair[index][1][self.loc.Y]
        self.pppair.sort(key=lambda com_x:com_x[self.loc.X],reverse=True)
        a_width=self.pppair[index][0][self.loc.X]-self.pppair[index][1][self.loc.X]
        return a_height*a_width

class AimMat(AimImageToolBox):
    def __init__(self,src_img):
        super(AimMat,self).__init__(src_img)
        self.preprocess()
        self.setfilter(2.55,2.75)
        self.filter()

if __name__=='__main__':
    mat=cv2.imread('../data/miao3.jpg')
    aim=AimMat(mat)
    pplen=aim.getlen()
    print(pplen)
    aim.showoff()
    cv2.waitKey(0)