import autoaim
import time
fps_last_timestamp = time.time()
fpscount = 0
fps = 0
camera = autoaim.Camera('data/test19.mp4')
capture = camera.capture
suc = True
while suc:
    suc, new_img = capture.read()
    fpscount = fpscount % 50 + 1
    if fpscount == 50:
        fps = 50/(time.time() - fps_last_timestamp)
        fps_last_timestamp = time.time()
        print("fps: ", fps)
