import cv2
cap = cv2.VideoCapture(0)
cap.set(3, 1024)
cap.set(4, 768)
i = 0
with open('data/calibration.txt', 'w') as f:
    while True:
        _, img = cap.read()
        cv2.imshow('capture', img)
        key = cv2.waitKey(10)
        print(key)
        if key == 102:
            path = 'data/calibration/img{}.png'.format(i)
            cv2.imwrite(path, img)
            print(path, file=f)
            i += 1
        elif key == 113:
            break
