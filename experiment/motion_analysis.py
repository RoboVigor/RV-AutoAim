# 分析云台系统的冲激响应 (输出增量观察装甲板在图像中的运动)
import autoaim
import cv2
import time
import threading
import sys
from toolz import curry, pipe
import os


# Global var
new_img = None
new_packet = None
aim = True
ww = 1280
hh = 720
# ww = 640
# hh = 360

data_path = os.path.abspath(__file__ + '/../../data')
with open(data_path+'/motion_analysis.csv', 'w') as f:
    f.write(str(time.time())+'\n')


def save(list):
    global data_path
    with open(data_path+'/motion_analysis.csv', 'a') as f:
        for line in list:
            f.write(str(line)+'\n')


def predict_movement(last, new):
    del last[0]
    last += [new]
    speed = []
    for i in range(len(last)-1):
        speed += [last[i+1] - last[i]]
    return sum(speed)/len(speed)


def predict_clear(last):
    return [0 for i in range(len(last))]


def moving_average(last, new):
    r = sum(last)/len(last)*0.25+new*0.75
    del last[0]
    last += [new]
    return r


def dead_region(val, range):
    # dead region
    if val > -range and val < range:
        return 0
    else:
        return val


pid_output_i = 0
last_error = None


def pid_control(target, feedback, pid_args=None):
    global pid_output_i, last_error
    if pid_args is None:
        pid_args = (1, 0.01, 4, 0.5)
    p, i, d, i_max = pid_args
    error = target-feedback
    if last_error is None:
        last_error = error
    pid_output_p = error*p
    pid_output_i += error*i
    pid_output_i = min([max([pid_output_i, -i_max]), i_max])
    pid_output_d = (error - last_error)*d
    return pid_output_p+pid_output_i+pid_output_d


def load_img():
    # set up camera
    global aim, new_img, ww, hh
    camera = autoaim.Camera(0)
    capture = camera.capture
    capture.set(3, ww)
    capture.set(4, hh)
    capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    capture.set(cv2.CAP_PROP_EXPOSURE, 1)
    while aim:
        suc, new_img = capture.read()


def send_packet():
    global new_packet
    while True:
        if new_packet is None:
            time.sleep(0.001)
            continue
        packet = new_packet
        new_packet = None
        # print(packet)
        autoaim.telegram.send(packet, port='/dev/ttyUSB0')


def aim_enemy():
    def aim(serial=True, lamp_weight='weights/lamp.csv', pair_weight='weights/pair.csv', angle_weight='weights/angle.csv', mode='red', gui_update=None):
        ##### set up var #####
        global aim, new_img, new_packet, ww, hh
        # experiment
        nb_start_time = time.time()
        nb_output_x = 10
        nb_original_position = 0
        nb_counter = 0
        result = []
        # autoaim
        predictor = autoaim.Predictor(lamp_weight, pair_weight, angle_weight)
        x_last = [0, 0, 0]
        y_last = [0, 0, 0]
        x_pred = [0 for i in range(7)]
        y_fix = 0
        packet_seq = 0
        shoot_seq = 0
        motion_last_timestamp = time.time()-1
        target_coordinate = (ww/2, hh/2)
        # fps
        fps_last_timestamp = time.time()
        fpscount = 0
        fps = 0
        while True:
            ##### load image #####

            if new_img is None:
                time.sleep(0.001)
                continue
            img = new_img
            new_img = None

            ##### locate target #####

            aimmat = predictor.predict(
                img,
                mode=mode,
                debug=False,
                lamp_threshold=0.01
            )
            # filter out the true lamp
            lamps = aimmat.lamps
            pairs = aimmat.pairs
            # sort by confidence
            lamps.sort(key=lambda x: x.y)
            pairs.sort(key=lambda x: x.y)

            ##### analysis target #####

            lost = len(lamps) == 0
            if lost:
                # target lost
                x, y, w, h = (0, 0, 0, 0)
                target = (ww/2, hh/2)
                target_coordinate = (ww/2, hh/2)
                shoot_seq = 0
                predict_clear(x_pred)
            else:
                # target found
                x, y, w, h = (0, 0, 0, 0)
                if len(pairs) > 1:
                    pair = None
                    top_score = pairs[-1].y
                    min_distance = ww*ww+hh*hh
                    close_score = 0
                    close_pair = None
                    for pair in pairs:
                        x1, y1, w1, h1 = pair.bounding_rect
                        x_diff = abs(target_coordinate[0]-x1)
                        y_diff = abs(target_coordinate[1]-y1)
                        distance = x_diff*x_diff + y_diff*y_diff
                        if distance < min_distance:
                            min_distance = distance
                            close_score = pair.y
                            close_pair = pair
                    if top_score > close_score + 0.3:
                        pair = pairs[-1]
                        predict_clear(x_pred)
                    else:
                        pair = close_pair
                    x, y, w, h = pair.bounding_rect
                    aimmat.pairs = [pair]
                elif len(pairs) == 1:
                    x, y, w, h = pairs[0].bounding_rect
                elif len(lamps) > 1:
                    x1, y1, w1, h1 = lamps[-1].bounding_rect
                    x2, y2, w2, h2 = lamps[-2].bounding_rect
                    x = (x1+x2)/2
                    y = (y1+y2)/2
                    w = (w1+w2)/2
                    h = (h1+h2)/2
                elif len(lamps) == 1:
                    x, y, w, h = lamps[0].bounding_rect

                ##### fix ballistic curve #####
                y_fix = 0

                # distance
                if ww == 1280:
                    # d = 35.69*(h**-0.866)
                    d = 27.578*(h**-0.841)
                elif ww == 640:
                    # d = 35.69*((h*2)**-0.866)
                    d = 27.578*((h*2)**-0.841)

                # antigravity
                if d > 1.5:
                    y_fix -= (1.07*d*d+2.65*d-6.28)/5.5*h
                    # y_fix -= (1.0424*x*x*x-8.8525*x*x+26.35*x-18.786)/5.5*h

                # distance between camera and barrel
                y_fix -= h/5.5*8

                # set target
                target_coordinate = (x+w/2, y+h/2)
                target = (x+w/2, y+h/2+y_fix)

                # motion predict
                pred = predict_movement(x_pred, target[0])
                # target = (target[0]+pred*30, target[1])

                ##### set kinestate #####
                x = target[0]/ww - 0.5
                y = target[1]/hh - 0.5

                # avarage value
                x = moving_average(x_last, x)
                y = moving_average(y_last, y)

                # decide to shoot
                if abs(x) < 0.03 and abs(y) < 0.03:
                    shoot_seq = 1
                else:
                    shoot_seq = 0

            ##### serial output #####
            if time.time()-nb_start_time > 1:
                print(nb_output_x)
                result += [(nb_original_position-target[0])/float(nb_counter)]
                nb_original_position = target[0]
                nb_output_x += 1
                nb_start_time = time.time()
                nb_counter = 0
            if nb_output_x == 15:
                save(result)
                break
            new_packet = autoaim.telegram.pack(
                0x0401, [float(nb_output_x/50), 0, bytes([shoot_seq])], seq=packet_seq)
            packet_seq = (packet_seq+1) % 256
            # print(nb_original_position-target[0])
            # print(x)
            # result += [nb_original_position-target[0]]
            nb_counter += 1

            ##### calculate fps #####
            fpscount = fpscount % 10 + 1
            if fpscount == 10:
                # print('pred:', pred*10, x)
                fps = 10/(time.time() - fps_last_timestamp)
                fps_last_timestamp = time.time()
                # print("fps: ", fps)

            ##### GUI #####
            if (not gui_update is None) and gui_update(fpscount):
                # print("out: ", x, y, shoot_seq)
                # print("height: ", h, w)
                pipe(
                    img.copy(),
                    # aimmat.mat.copy(),
                    # aimmat.binary_mat.copy(),
                    aimmat.draw_contours,
                    aimmat.draw_bounding_rects,
                    # aimmat.draw_texts()(lambda l: '{:.2f}'.format(l.y)),
                    # aimmat.draw_texts()(
                    #     lambda l: '{:.2f}'.format(l.bounding_rect[3])),
                    aimmat.draw_pair_bounding_rects,
                    aimmat.draw_pair_bounding_text()(
                        lambda l: '{:.2f}'.format(l.y)
                    ),
                    # curry(aimmat.draw_centers)(center=(ww/2, hh/2)),
                    curry(aimmat.draw_centers)(
                        center=(target[0]+pred*30, target[1])),
                    # curry(aimmat.draw_centers)(center=(ww/2, hh/2-y_fix)),
                    aimmat.draw_fps()(int(fps)),
                    aimmat.draw_target()((target[0], target[1])),
                    curry(autoaim.helpers.showoff)(timeout=1, update=True)
                )
    return curry(aim)


if __name__ == '__main__':

    def gui_update(x): return x % 10 == 0
    if len(sys.argv) > 1 and sys.argv[1] == 'production':
        threading.Thread(target=load_img).start()
        threading.Thread(target=send_packet).start()
        threading.Thread(target=aim_enemy()(
            serial=True,
            mode='red',
            gui_update=None)).start()
    else:
        threading.Thread(target=load_img).start()
        threading.Thread(target=send_packet).start()
        threading.Thread(target=aim_enemy()(
            serial=True,
            mode='red',
            gui_update=lambda x: x % 10 == 0)).start()
    print("THE END.")
