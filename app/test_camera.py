import autoaim
import cv2
import time
import threading


# global var
aim = True
new_img = None
ww = 1280
hh = 720
fpscount = 0


# func


def moving_average(last, new):
    r = sum(last)/len(last)*0.3+new*0.7
    del last[0]
    last += [new]
    return r


def load_img():
    # set up camera
    global aim, new_img, ww, hh, fpscount
    camera = autoaim.Camera(1)
    capture = camera.capture
    capture.set(3, ww)
    capture.set(4, hh)
    capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    capture.set(cv2.CAP_PROP_EXPOSURE, -9)
    while aim:
        suc, new_img = capture.read()
        fpscount += 1


def aim_enemy():
    # aim
    global aim, new_img, ww, hh, fpscount
    x_last = [0, 0, 0]
    y_last = [0, 0, 0]
    predictor = autoaim.Predictor('weight8.csv')
    img = None
    # fps analysis
    seq = 0
    last_timestamp = time.time()
    duration = 1
    while aim:
        threadLock.acquire()
        if new_img is None:
            threadLock.release()
            continue
        if fpscount == 50:
            duration = time.time() - last_timestamp
            last_timestamp = time.time()
            print("fps: ", 50/duration)


# thread
threadLock = threading.Lock()
threads = []
t1 = threading.Thread(target=load_img)
threads.append(t1)
t2 = threading.Thread(target=aim_enemy)
threads.append(t2)

if __name__ == '__main__':
    for t in threads:
        t.start()
    print("all over")
