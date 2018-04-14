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
#include <unistd.h>
#include <fcntl.h>

class LedController {
public:
    LedController(char * gpio_path){
        //fd2led = open("/sys/class/gpio/gpio158/value", O_WRONLY);
        fd2led = open(gpio_path, O_WRONLY);
    }
    void ledON(){
        write(fd2led, "1", 2);
    }
    void ledOFF(){
        write(fd2led, "0", 2);
    }
    void ledflash(int time){
        if (time > flash_cnt){
            led_status = !led_status;
            flash_cnt = 0;
        }
        if (led_status)
            ledON();
        else
            ledOFF();
        ++flash_cnt;
    }

public:
    bool led_status;
    int flash_cnt;
    int fd2led;
};

