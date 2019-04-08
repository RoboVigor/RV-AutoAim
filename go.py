import autoaim
import cv2
w = 1024
h = 768
camera = autoaim.Camera(0)
capture = camera.capture
capture.set(3, w)
capture.set(4, h)
suc,img = capture.read()
# autoaim.helpers.showoff(img)
# cv2.waitKey(-1)
for i in range(0, 10000):
    suc,img = capture.read()
    predictor = autoaim.Predictor('weight8.csv')
    lamps = predictor.predict(img, mode='red', debug=True)
    lamps.sort(key=lambda x: x.y)
    if len(lamps)>0:
        x1,y1,w1,w1 = lamps[0].bounding_rect
        print('---------')
        output = (x1+w1/2-w/2)/w*20
        output = int(output+128)
        print(output-128)
        autoaim.serial.send([output])
