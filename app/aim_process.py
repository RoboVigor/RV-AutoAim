# -*- coding: utf-8 -*-
'''多线程自瞄

Author:
'''
import autoaim
import cv2
import time
from multiprocessing import Process, Queue
import sys
from toolz import curry, pipe
import importlib


def miao(val, minval, maxval):
    return min(max(val, minval), maxval)


def moving_average(last, new):
    empty = False
    for x in last:
        if not x == 0:
            empty = True
    if empty:
        for i in range(len(last)):
            last[i] = new
    else:
        del last[0]
        last += [new]
    return sum(last)/len(last)


def read_image(app_config, image_queue):
    app_config = autoaim.AttrDict(app_config)
    # set up camera
    resolution = (app_config.width, app_config.height)
    source = app_config.camera.source
    method = app_config.camera.method
    # set up fps_count
    fps_last_timestamp = time.time()
    fpscount = 0
    fps = 0
    print('using: {}@{} at {}'.format(source, method, resolution))
    # read from camera
    if method == 'daheng':
        gx = importlib.import_module('gxipy')
        device_manager = gx.DeviceManager()
        dev_num, dev_info_list = device_manager.update_device_list()
        if dev_num == 0:
            sys.exit(1)
        str_index = dev_info_list[0].get("index")
        cam = device_manager.open_device_by_index(str_index)
        cam.Width.set(resolution[0])
        cam.Height.set(resolution[1])
        cam.stream_on()
        while True:
            raw_image = cam.data_stream[0].get_image()
            new_img = raw_image.convert('RGB').get_numpy_array()[..., ::-1]
            image_queue.put(new_img)
            fpscount = fpscount % 100 + 1
            if fpscount == 100:
                fps = 100/(time.time() - fps_last_timestamp+0.0001)
                fps_last_timestamp = time.time()
                print("fps: ", fps)
    else:
        camera = autoaim.Camera(source, method)
        camera.init(resolution)
        while True:
            success, image = camera.get_image()
            if success:
                image_queue.put(image)
                fpscount = fpscount % 100 + 1
                if fpscount == 100:
                    fps = 100/(time.time() - fps_last_timestamp+0.0001)
                    fps_last_timestamp = time.time()
                    print('fps: ', fps)
            else:
                print('error reading image')
                break


def send_packet(app_config, packet_queue):
    app_config = autoaim.AttrDict(app_config)
    while True:
        try:
            packet = packet_queue.get(timeout=5000)
            autoaim.telegram.send(packet, port='/dev/ttyUSB0')
        except:
            print('exit:send_packet')
            break


def aim_enemy(app_config, image_queue, packet_queue):
    app_config = autoaim.AttrDict(app_config)
    ##### set up var #####
    # config
    center = (app_config.width/2, app_config.height/2)
    threshold_target_changed = 0.5
    distance_to_laser = 12
    x_fix = -15
    threshold_shoot = 0.03
    threshold_position_changed = 70
    # autoaim
    track_state = 0  # 0:tracking, 1:lost
    config = autoaim.Config().read(app_config.toolbox_config.config_name)
    predictor = autoaim.Predictor(config)
    last_pair = None
    pair = None
    height_record_list = ([0 for i in range(10)])
    y_fix = 0
    packet_seq = 0
    shoot_it = 0
    target = (app_config.width/2, app_config.height/2)
    target_yfix = (app_config.width/2, app_config.height/2)
    output = (0, 0)
    # fps
    fps_last_timestamp = time.time()
    fpscount = 0
    fps = 0
    while True:
        ##### load image #####

        img = image_queue.get()

        ##### locate target #####

        toolbox = predictor.predict(img, debug=False)
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
            target = (app_config.width/2, app_config.height/2)
            target_yfix = (app_config.width/2, app_config.height/2)
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
                    x_diff = abs(x1+w1/2-app_config.width/2)
                    y_diff = abs(y1+h1/2-app_config.height/2)
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

        # resolve angle
        # target_undistort = toolbox.undistort_points([target_yfix])[0][0]
        angle = toolbox.calc_point_angle(target_yfix, center)
        output = [float(angle[0]/10), float(angle[1]/10)]
        output = [miao(output[0], -1.5, 1.5),
                  miao(output[1], -1.2, 1.2)]

        # decide to shoot
        if abs(angle[0]) < threshold_shoot and abs(angle[1]) < threshold_shoot and track_state == 1:
            shoot_it = 1
        else:
            shoot_it = 0

        ##### serial output #####
        packet = autoaim.telegram.pack(
            0x0401, [*output, bytes([shoot_it])], seq=packet_seq)
        if packet_queue.full():
            packet_queue.get_nowait()
        packet_queue.put_nowait(packet)
        packet_seq = (packet_seq+1) % 256
        # print('{0:.2f} {1:.2f}'.format(*output))

        ##### calculate fps #####
        fpscount = fpscount % 100 + 1
        if fpscount == 100:
            fps = 100/(time.time() - fps_last_timestamp)
            fps_last_timestamp = time.time()
            # print('cal fps: ', fps)

        ##### GUI #####
        if app_config.gui_update and fpscount % app_config.gui_update == 0:
            # print('out: ', x, y, shoot_it)
            # print('height: ', h, w)
            pipe(
                img,
                # toolbox.mat.grayscale,
                toolbox.draw_contours,
                # toolbox.draw_bounding_rects,
                toolbox.draw_texts()(lambda l: l.bounding_rect[3]),
                toolbox.draw_pair_bounding_rects,
                # toolbox.draw_pair_bounding_text()(
                #     lambda l: '{:.2f}'.format(l.angle)
                # ),
                curry(toolbox.draw_centers)(center=center),
                toolbox.draw_target()(target),
                toolbox.draw_fps()(int(fps)),
                curry(autoaim.helpers.showoff)(timeout=1, update=True)
            )


if __name__ == '__main__':
    app_config_dict = {
        'toolbox_config': {
            'config_name': 'default'
        },
        'camera': {
            'source': 0,
            'method': 'daheng'
            # 'source': 'data/test19.mp4'
        },
        'width': 968,
        'height': 720,
        'serial': False,
        'gui_update': 30
    }
    app_config = autoaim.AttrDict(app_config_dict)
    for arg in sys.argv:
        if arg == 'production':
            app_config.serial = True
            app_config.gui_update = None
        if arg == 'debug':
            app_config.serial = True
        elif arg == 'red':
            app_config.config.target_color = 'red'
        elif arg == 'blue':
            app_config.config.target_color = 'blue'
        elif arg == 'white':
            app_config.config.target_color = 'white'
        elif arg == 'analysis':
            app_config.analysis = True
    print(app_config.data)

    image_queue = Queue(3)
    packet_queue = Queue(3)

    Process(target=read_image, args=[app_config_dict, image_queue]).start()
    Process(target=aim_enemy, args=[app_config_dict,
                                    image_queue, packet_queue]).start()
    if app_config.serial:
        Process(target=send_packet, args=[
            app_config_dict, packet_queue]).start()
