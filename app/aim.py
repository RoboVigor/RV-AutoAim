import autoaim
import cv2
w = 1024
h = 768
camera = autoaim.Camera(0)
capture = camera.capture
capture.set(3, w)
capture.set(4, h)
suc, img = capture.read()
# autoaim.helpers.showoff(img)
# cv2.waitKey(-1)


def moving_average(last, new):
    r = sum(last)/len(last)*0.6+new*0.4
    del last[0]
    last += [new]
    return r


x_last = [0, 0, 0, 0, 0]
y_last = [0, 0, 0]

while True:
    suc, img = capture.read()
    predictor = autoaim.Predictor('weight8.csv')
    lamps = predictor.predict(img, mode='red', debug=True)
    lamps.sort(key=lambda x: x.y)
    if len(lamps) > 0:
        x1, y1, w1, h1 = lamps[-1].bounding_rect
        print('---------')
        # current
        x = (2*x1+w1-w)/w
        y = (2*y1+h1-h)/h
        # avarage
        x = moving_average(x_last, x)
        y = moving_average(y_last, y)

        # output
        x = round(x*15)
        y = round(y*-4)
        print(x, y)
        output = (x+15) << 3 | (y+3)
        #autoaim.telegram.send([output], port='COM6')
