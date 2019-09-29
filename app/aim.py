import autoaim
import cv2
import time

ww = 1280
hh = 720
camera = autoaim.Camera(0)
capture = camera.capture
capture.set(3, ww)
capture.set(4, hh)
# suc, img = capture.read()
# autoaim.helpers.showoff(img)
# cv2.waitKey(-1)


def moving_average(last, new):
    r = sum(last)/len(last)*0.3+new*0.7
    del last[0]
    last += [new]
    return r


x_last = [0, 0, 0]
y_last = [0, 0, 0]

seq = 0
fpscount = 0
last_timestamp = time.time()
duration = 1
while True:
    suc, img = capture.read()
    predictor = autoaim.Predictor('weight9.csv', 'pair_weight.csv')
    aimmat = predictor.predict(
        img, mode='red', debug=fpscount % 10 == 0, timeout=1)
    lamps = aimmat.lamps
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
    packet = autoaim.telegram.pack(0x0401, [x*10, -y*3], seq=seq)
    seq = (seq+1) % 256
    # autoaim.telegram.send(packet)
    # cv2.waitKey(10)

    # calc fps
    fpscount = seq % 50 + 1
    if fpscount == 50:
        duration = time.time() - last_timestamp
        last_timestamp = time.time()
        print("fps: ", 50/duration)

    # print('---------')
    #print(x*30, y)
