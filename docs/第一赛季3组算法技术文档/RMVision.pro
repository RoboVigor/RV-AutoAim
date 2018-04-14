##########################################################
#Copyright 2017 Dajiang Innovations Technology Co., Ltd (DJI)
#
#Permission is hereby granted, free of charge, to any person #obtaining a copy of this software and associated 
#documentation files (the "Software"), to deal in the Software #without restriction, including without limitation 
#the rights to use, copy, modify, merge, publish, distribute, #sublicense, and/or sell copies of the Software, and 
#to permit persons to whom the Software is furnished to do so, #subject to the following conditions: 
#
#The above copyright notice and this permission notice shall be #included in all copies or substantial portions of 
#the Software.
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, #EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO 
#THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR #PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES #OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
#CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN #CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
#IN THE SOFTWARE.
##############################################################














TEMPLATE = app
CONFIG += console
CONFIG -= app_bundle
CONFIG -= qt
CONFIG += c++11
QMAKE_CXXFLAGS_RELEASE += -O3

QMAKE_CXXFLAGS += -mfloat-abi=hard -mfpu=neon -march=armv7-a -marm -mthumb-interwork
QMAKE_CFLAGS += -mfloat-abi=softfp -mfpu=neon -march=armv7-a -marm -mthumb-interwork

INCLUDEPATH += -I/usr/local/include/opencv \
               -I/usr/local/include

LIBS += -L/usr/local/lib -lopencv_shape -lopencv_stitching -lopencv_superres -lopencv_videostab -lopencv_calib3d -lopencv_features2d -lopencv_objdetect -lopencv_highgui -lopencv_videoio -lopencv_photo -lopencv_imgcodecs -lopencv_video -lopencv_ml -lopencv_imgproc -lopencv_flann -lopencv_core -lopencv_hal

SOURCES += main.cpp \
    serial.cpp \
    RuneDetector.cpp \
    RuneResFilter.cpp \
    ArmorDetector.cpp \
    Predictor.cpp \
    ImageConsProd.cpp \
    RemoteController.cpp \
    AngleSolver.cpp \
    RMVideoCapture.cpp

HEADERS += \
    serial.h \
    cmdline.h \
    RuneDetector.hpp \
    RuneResFilter.hpp \
    Settings.hpp \
    ArmorDetector.hpp \
    Predictor.hpp \
    ImageConsProd.hpp \
    RemoteController.hpp \
    AngleSolver.hpp \
    sse_to_neon.hpp \
    RMVideoCapture.hpp \
    LedController.hpp

