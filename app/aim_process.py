# -*- coding: utf-8 -*-
'''多进程自瞄
https://stackoverflow.com/questions/7894791/use-numpy-array-in-shared-memory-for-multiprocessing
https://stackoverflow.com/questions/9754034/can-i-create-a-shared-multiarray-or-lists-of-lists-object-in-python-for-multipro
Author:
'''
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+'/../')
import autoaim
import app
from multiprocessing import Process, Queue
import sys
from shared_arrays import ArrayQueue

shared_data = []


if __name__ == '__main__':
    app_config = {
        'config_name': 'default',
        'camera': {
            'source': 0,
            'method': 'daheng',
            # 'method': 'default',
            # 'source': 'test19.mp4',
            # 'method': 'video',
        },
        # 'width': 1280,
        # 'height': 1024,
        'width': 960,
        'height': 768,
        'serial': True,
        'gui_update_every': 10,
        # 'stop_after': 300,
        'stop_after': float('inf'),
        "lamp_weight": 'lamp.csv',
        "pair_weight": 'pair.csv'
    }
    for arg in sys.argv:
        if arg == 'production':
            app_config['serial'] = True
            app_config['gui_update_every'] = None
        if arg == 'debug':
            app_config['serial'] = True
        elif arg == 'red':
            app_config['target_color'] = 'red'
        elif arg == 'blue':
            app_config['target_color'] = 'blue'
        elif arg == 'white':
            app_config['target_color'] = 'white'
        elif arg == 'analysis':
            app_config['analysis'] = True
    print(app_config)

    image_queue = ArrayQueue(50, 3)
    packet_queue = Queue(3)

    processes = []
    processes += [Process(
        target=app.aim_enemy,
        args=[
            app_config,
            image_queue,
            packet_queue
        ])]
    processes += [Process(
        target=app.read_image,
        args=[
            app_config,
            image_queue
        ])]
    if app_config['serial']:
        processes += [Process(
            target=app.send_packet,
            args=[
                app_config,
                packet_queue
            ])]

    for process in processes:
        process.start()
    for process in processes:
        process.join()
