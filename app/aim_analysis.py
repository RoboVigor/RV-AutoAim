import autoaim
import cv2
import time
import threading
from toolz import curry


# global var
new_img = None
aim = True
ww = 1280
hh = 720


def moving_average(last, new):
    r = sum(last)/len(last)*0.3+new*0.7
    del last[0]
    last += [new]
    return r


def load_img():
    # set up camera
    global aim, new_img, ww, hh
    camera = autoaim.Camera(0)
    capture = camera.capture
    capture.set(3, ww)
    capture.set(4, hh)
    capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    capture.set(cv2.CAP_PROP_EXPOSURE, -9)
    # suc, img = capture.read()
    # autoaim.helpers.showoff(img)
    # cv2.waitKey(-1)
    while aim:
        suc, new_img = capture.read()


def aim_enemy():
    def aim(serial_output=True, debugint=lambda x: x % 20 == 0):
        global aim, new_img, ww, hh
        # autoaim
        predictor = autoaim.Predictor('weight9.csv')
        x_last = [0, 0, 0]
        y_last = [0, 0, 0]
        packet_seq = 0
        # fps
        last_timestamp = time.time()
        fpscount = 0
        # quit
        quit_counter = 0
        while quit_counter < 500:
            if new_img is None:
                time.sleep(0.001)
                continue
            img = new_img
            new_img = None
            quit_counter += 1
            # autoaim
            lamps = predictor.predict(
                img, mode='red', debug=debugint(fpscount), timeout=1)
            lamps.sort(key=lambda x: x.y)
            x, y, w, h = (0, 0, 0, 0)
            lamps = [l for l in lamps if l.y > 0.15]
            if len(lamps) == 1:
                x, y, w, h = lamps[-1].bounding_rect
            elif len(lamps) > 1:
                x1, y1, w1, h1 = lamps[-1].bounding_rect
                x2, y2, w2, h2 = lamps[-2].bounding_rect
                x = (x1+x2)/2
                y = (y1+y2)/2
                w = (w1+w2)/2
                h = (h1+h2)/2

            # current
            x = (x+w/2)/ww - 0.5
            y = (y+h/2)/hh - 0.5

            # avarage
            x = moving_average(x_last, x)
            y = moving_average(y_last, y)

            # output
            packet = autoaim.telegram.pack(
                0x0401, [x*20, -y*6], seq=packet_seq)
            packet_seq = (packet_seq+1) % 256
            if serial_output:
                autoaim.telegram.send(packet)
            # cv2.waitKey(10)

            # calc fps
            fpscount = fpscount % 50 + 1
            if fpscount == 50:
                print("fps: ", 50/(time.time() - last_timestamp))
                last_timestamp = time.time()
        aim = False
    return curry(aim)


if __name__ == '__main__':
    threading.Thread(target=load_img).start()
    threading.Thread(target=aim_enemy()(serial_output=False)).start()
    print("THE END.")
