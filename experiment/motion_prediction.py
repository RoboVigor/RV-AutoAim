# 用于运动预测：加载数据集显示一定时间后装甲板的位置
import autoaim
import cv2
import time
import threading
import sys
from toolz import curry, pipe


# Global var
new_img = None
new_packet = None
aim = True
ww = 1280
hh = 720
# ww = 640
# hh = 360

start = 150
stop = 500

good_index = 0
good_dict = {}


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


def aim_enemy():
    def aim(serial=True, lamp_weight='weight9.csv', pair_weight='pair_weight.csv', mode='red', gui_update=None):
        ##### set up var #####
        global aim, new_img, new_packet, ww, hh
        # autoaim
        predictor = autoaim.Predictor(lamp_weight, pair_weight)
        x_last = [0, 0, 0]
        y_last = [0, 0, 0]
        x_pred = [0 for i in range(7)]
        y_fix = 0
        packet_seq = 0
        shoot_seq = 0
        motion_last_timestamp = time.time()
        target_coordinate = (ww/2, hh/2)
        # fps
        fps_last_timestamp = time.time()
        fpscount = 0
        fps = 0
        ########################################
        ########################################
        ########################################
        ########################################
        ########################################

        for iii in range(start, stop):

            ##### load image #####
            img_url = 'data/test13/{}.jpeg'.format(iii)
            print('Load {}'.format(img_url))
            img = autoaim.helpers.load(img_url)

            ##### locate target #####

            feature = predictor.predict(
                img,
                mode=mode,
                debug=False,
                lamp_threshold=0.01
            )
            # filter out the true lamp
            lamps = feature.lamps
            pairs = feature.pairs
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
                    min_distance = ww+hh
                    close_score = 0
                    close_pair = None
                    for pair in pairs:
                        x1, y1, w1, h1 = pair.bounding_rect
                        x_diff = abs(target_coordinate[0]-x1)
                        y_diff = abs(target_coordinate[1]-y1)
                        distance = x_diff + y_diff
                        if distance < min_distance:
                            min_distance = distance
                            close_score = pair.y
                            close_pair = pair
                    if top_score > close_score + 0.35:
                        pair = pairs[-1]
                        predict_clear(x_pred)
                    else:
                        pair = close_pair
                    x, y, w, h = pair.bounding_rect
                    feature.pairs = [pair]
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
                target_coordinate = (x+w/2, y+h/2+y_fix)
                target = (x+w/2, y+h/2)
                good_dict[iii] = target
        ########################################
        ########################################
        ########################################
        ########################################
        ########################################
        for iii in range(start, stop):
            ##### load image #####

            img_url = 'data/test13/{}.jpeg'.format(iii)
            print('Load {}'.format(img_url))
            img = autoaim.helpers.load(img_url)

            ##### locate target #####

            feature = predictor.predict(
                img,
                mode=mode,
                debug=False,
                lamp_threshold=0.01
            )
            # filter out the true lamp
            lamps = feature.lamps
            pairs = feature.pairs
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
                    min_distance = ww+hh
                    close_score = 0
                    close_pair = None
                    for pair in pairs:
                        x1, y1, w1, h1 = pair.bounding_rect
                        x_diff = abs(target_coordinate[0]-x1)
                        y_diff = abs(target_coordinate[1]-y1)
                        distance = x_diff + y_diff
                        if distance < min_distance:
                            min_distance = distance
                            close_score = pair.y
                            close_pair = pair
                    if top_score > close_score + 0.35:
                        pair = pairs[-1]
                        predict_clear(x_pred)
                    else:
                        pair = close_pair
                    x, y, w, h = pair.bounding_rect
                    feature.pairs = [pair]
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
                target_coordinate = (x+w/2, y+h/2+y_fix)
                target = (x+w/2, y+h/2)

                ##### set kinestate #####
                x = target[0]/ww - 0.5
                y = target[1]/hh - 0.5

                # avarage value
                x = moving_average(x_last, x)
                y = moving_average(y_last, y)

                # motion predict
                pred = predict_movement(x_pred, target[0])
                # x += pred*10

                # decide to shoot
                if abs(x) < 0.03 and abs(y) < 0.03:
                    shoot_seq = 1
                else:
                    shoot_seq = 0

            ##### calculate fps #####
            fpscount = fpscount % 10 + 1
            if fpscount == 10:
                # print('pred:', pred*10, x)
                fps = 10/(time.time() - fps_last_timestamp)
                fps_last_timestamp = time.time()
                print("fps: ", fps)

            ##### GUI #####
            if (not gui_update is None) and gui_update(fpscount):
                # print("out: ", x, y, shoot_seq)
                # print("height: ", h, w)
                print(pred)
                pipe(
                    img.copy(),
                    # feature.mat.copy(),
                    # feature.binary_mat.copy(),
                    feature.draw_contours,
                    feature.draw_bounding_rects,
                    # feature.draw_texts()(lambda l: '{:.2f}'.format(l.y)),
                    # feature.draw_texts()(
                    #     lambda l: '{:.2f}'.format(l.bounding_rect[3])),
                    feature.draw_pair_bounding_rects,
                    feature.draw_pair_bounding_text()(
                        lambda l: '{:.2f}'.format(l.y)
                    ),
                    curry(feature.draw_centers)(
                        center=(good_dict[iii+10][0], good_dict[iii+10][1])),
                    curry(feature.draw_centers)(
                        center=(good_dict[iii+10][0], good_dict[iii+10][1])),
                    # feature.draw_fps()(int(good_dict[iii+10][0]*100)),
                    feature.draw_target()((target[0]+pred*12, target[1])),
                    curry(autoaim.helpers.showoff)(timeout=100, update=True)
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
        threading.Thread(target=aim_enemy()(
            serial=False,
            mode='red',
            gui_update=lambda x: True)).start()
    print("THE END.")
