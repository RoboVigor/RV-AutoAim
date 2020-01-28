# -*- coding: utf-8 -*-
"""Single-thread aim

Author:Tccoin
"""
import autoaim
import cv2
import time
from toolz import curry, pipe

ww = 1280
hh = 720


camera = autoaim.Camera('data/test19.mp4')
capture = camera.capture
fps_last_timestamp = time.time()
fpscount = 0
fps = 0
frames = []
suc = True
while True:
    suc, frame = capture.read()
    if suc:
        frames += [frame]
    else:
        break


def miao(val, minval, maxval):
    return min(max(val, minval), maxval)


def moving_average(last, new):
    r = sum(last)/len(last)*0.3+new*0.7
    del last[0]
    last += [new]
    return r


new_img = None
new_packet = None
aim = True
ww = 1280
hh = 720


def aim(img, serial=True, config_name='default', gui_update=False):
    ##### set up var #####
    global aim, new_packet, ww, hh
    # config
    threshold_target_changed = 0.5
    distance_to_laser = 12
    x_fix = -15
    threshold_shoot = 0.03
    threshold_position_changed = 70
    # autoaim
    track_state = 0  # 0:tracking, 1:lost
    config = autoaim.Config({'config_name': config_name}).read()
    predictor = autoaim.Predictor(config)
    last_pair = None
    pair = None
    height_record_list = ([0 for i in range(10)])
    y_fix = 0
    packet_seq = 0
    shoot_it = 0
    target = (ww/2, hh/2)
    target_yfix = (ww/2, hh/2)
    output = (0, 0)

    ##### locate target #####

    toolbox = predictor.predict(
        img,
        debug=False,
    )
    # filter out the true lamp
    lamps = toolbox.data.lamps
    pairs = toolbox.data.pairs
    # sort by confidence
    lamps.sort(key=lambda x: x.y)
    pairs.sort(key=lambda x: x.y_max)

    ##### analysis target #####

    # logic of losing target
    if len(lamps) == 0:
        # target lost
        track_state = 0
        x, y, w, h = (0, 0, 0, 0)
        last_pair = None
        target = (ww/2, hh/2)
        target_yfix = (ww/2, hh/2)
        shoot_it = 0
    else:
        # target found
        x, y, w, h = (0, 0, 0, 0)
        pair = None
        if len(pairs) > 1:
            pair = None
            # get track score
            pairid = 0
            for pair in pairs:
                pairid += 1
                x1, y1, w1, h1 = pair.bounding_rect
                x_diff = abs(target[0]-(x1+w1/2))
                y_diff = abs(target[1]-(y1+h1/2))
                target_distance = -(x_diff*x_diff + y_diff*y_diff)/5000
                x_diff = abs(x1+w1/2-ww/2)
                y_diff = abs(y1+h1/2-hh/2)
                distance = h1/50
                label = pair.y_label*-2
                score = pair.y_max*5+target_distance+label+distance
                pair.score = score
                pair.pairid = pairid
                # print([pairid, pair.y, target_distance, angle,label, distance, score])
            # set track state
            track_state = 1
            # decide the pair
            pairs = sorted(pairs, key=lambda x: x.score)
            last_pair = pair
            pair = pairs[-1]
            x, y, w, h = pair.bounding_rect
            toolbox.data.pairs = [p for p in pairs if p.y_label == 0]
            toolbox.data.pairs = [pair]
            # print('pair+')
        elif len(pairs) == 1:
            track_state = 1
            last_pair = pair
            pair = pairs[0]
            pair.score = 6.66
            pair.pairid = 1
            x, y, w, h = pair.bounding_rect
            # print('pair1')
        elif len(lamps) > 1:
            track_state = 1
            x1, y1, w1, h1 = lamps[-1].bounding_rect
            x2, y2, w2, h2 = lamps[-2].bounding_rect
            x = (x1+x2)/2
            y = (y1+y2)/2
            w = (w1+w2)/2
            h = (h1+h2)/2
            # print('lamps+')
        elif len(lamps) == 1:
            track_state = 0
            x, y, w, h = lamps[0].bounding_rect
            # print('lamps1')

        # detect pair changed
        if not last_pair is None and not pair is None:
            over_threshold = abs(
                last_pair.y_max-pair.y_max) > threshold_target_changed
            type_changed = not pair.y_label == last_pair.y_label
            _1 = last_pair.bounding_rect[0] + \
                last_pair.bounding_rect[2]/2
            _2 = pair.bounding_rect[0]+pair.bounding_rect[2]/2
            position_changed = abs(_1-_2) > threshold_position_changed
            if over_threshold or type_changed or position_changed:
                track_state = 0

        h = moving_average(height_record_list, h)

        # distance
        if ww == 1280:
            # 英雄
            # if mode == 'blue':
            #     d = 73.7*(h**-0.972)
            # else:
            #     d = 72.472*(h**-1.027)
            # 步兵
            d = 257.28*(h**-1.257)

        # antigravity
        y_fix = 0
        # y_fix -= (2.75*d*d -1.6845*d - 0.4286)/5.5*h # hero
        y_fix -= min(1.4777*d*d + -3.532*d - 2.1818, 8) / \
            5.5 * h  # infantry
        # print(d, y_fix)

        # distance between camera and barrel
        y_fix -= h/5.5*distance_to_laser

        # set target
        target = (x+w/2, y+h/2)
        target_yfix = (x+w/2+x_fix, y+h/2+y_fix)

        # decide to shoot
        x = target_yfix[0]/ww - 0.5
        y = target_yfix[1]/hh - 0.5
        if abs(x) < threshold_shoot and abs(y) < threshold_shoot and track_state == 1:
            shoot_it = 1
        else:
            shoot_it = 0

    ##### serial output #####
    output = toolbox.undistort_points([target_yfix])[0]
    output = toolbox.calc_point_angle(*output)
    output = [float(output[0]/10), float(output[1]/10)]
    output = [miao(output[0], -1.5, 1.5),
              miao(output[1], -1.2, 1.2)]
    # print(output)

    ##### GUI #####
    if gui_update:
        # print("out: ", x, y, shoot_it)
        # print("height: ", h, w)
        pipe(
            img,
            toolbox.draw_contours,
            toolbox.draw_bounding_rects,
            toolbox.draw_texts()(lambda l: l.bounding_rect[3]),
            toolbox.draw_pair_bounding_rects,
            # toolbox.draw_pair_bounding_text()(
            #     lambda l: '{:.2f}'.format(l.angle)
            # ),
            curry(toolbox.draw_centers)(center=(ww/2, hh/2)),
            toolbox.draw_target()(target),
            toolbox.draw_fps()(int(fps)),
            curry(autoaim.helpers.showoff)(timeout=1, update=True)
        )


for i in range(2):
    for new_img in frames:
        fpscount = fpscount % 100 + 1
        if fpscount == 100:
            fps = 100/(time.time() - fps_last_timestamp+0.0001)
            fps_last_timestamp = time.time()
            print("fps: ", fps)
        # aim(new_img, serial=False,
        #     config_name='default',
        #     gui_update=fpscount % 30 == 0)
        aim(new_img, serial=False,
            config_name='default')
