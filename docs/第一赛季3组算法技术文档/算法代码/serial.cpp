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

#include "serial.h"
//#include "utils.h"

#include <math.h>
#include <stdio.h>      // standard input / output functions
#include <string.h>     // string function definitions
#include <unistd.h>     // UNIX standard function definitions
#include <fcntl.h>      // File control definitions
#include <errno.h>      // Error number definitions
#include <termios.h>    // POSIX terminal control definitionss


int openPort(const char * dev_name){
    int fd; // file description for the serial port
    fd = open(dev_name, O_RDWR | O_NOCTTY | O_NDELAY);
    if(fd == -1){ // if open is unsucessful
        printf("open_port: Unable to open /dev/ttyS0. \n");
    }
    else  {
        fcntl(fd, F_SETFL, 0);
        printf("port is open.\n");
    }
    return(fd);
}

int configurePort(int fd){                      // configure the port
    struct termios port_settings;               // structure to store the port settings in
    cfsetispeed(&port_settings, B115200);       // set baud rates
    cfsetospeed(&port_settings, B115200);

    port_settings.c_cflag &= ~PARENB;           // set no parity, stop bits, data bits
    port_settings.c_cflag &= ~CSTOPB;
    port_settings.c_cflag &= ~CSIZE;
    port_settings.c_cflag |= CS8;

    tcsetattr(fd, TCSANOW, &port_settings);     // apply the settings to the port
    return(fd);
}

bool sendXYZ(int fd, double * xyz){
    unsigned char send_bytes[] = { 0xFF,0x00,0x00,0x00,0x00,0x00,0x00,0xFE};
    if(NULL == xyz){
        if (8 == write(fd, send_bytes, 8))  //Send data
            return true;
        return false;
    }
    short * data_ptr = (short *)(send_bytes + 1);
    data_ptr[0] = (short)xyz[0];
    data_ptr[1] = (short)xyz[1];
    data_ptr[2] = (short)xyz[2];
    if (8 == write(fd, send_bytes, 8))      //Send data
        return true;
    return false;
}

bool sendData(int fd, char * data, int size, DATATYPE data_tpye){
    unsigned char header[5];
    int * _size = (int *)header;
    _size[0] = size;
    unsigned char * _type = header+4;
    _type[0] = data_tpye;
    if (5 != write(fd, header, 5)){
        printf("send Data error\n");
        return false;
    }
    if (size == write(fd, data, size)){
        printf("send Data success\n");
        return true;
    }
    return false;
}

