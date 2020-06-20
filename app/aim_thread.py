# -*- coding: utf-8 -*-
'''multi-threading aim

Author:
'''
import autoaim
import app
import threading
import sys
import queue


if __name__ == '__main__':
    app_config = {
        'config_name': 'default',
        'camera': {
            'source': 0,
            # 'method': 'daheng',
            # 'method': 'default',
            'source': autoaim.helpers.data_dir+'test19.mp4',
            'method': 'video',
        },
        'width': 1280,
        'height': 1024,
        'serial': False,
        'gui_update_every': 10,
        # 'stop_after': 300,
        'stop_after': float('inf'),
        "lamp_weight": 'lamp.csv',
        "pair_weight": 'pair.csv'
    }
    image_queue = queue.Queue(3)
    packet_queue = queue.Queue(3)
    for arg in sys.argv:
        if arg == 'production':
            app_config['serial'] = True
            app_config['gui_update_Every'] = None
        if arg == 'debug':
            app_config['serial'] = True
        elif arg == 'red':
            app_config['config']['target_color'] = 'red'
        elif arg == 'blue':
            app_config['config']['target_color'] = 'blue'
        elif arg == 'white':
            app_config['config']['target_color'] = 'white'
        elif arg == 'analysis':
            app_config['analysis'] = True
    print(app_config, '\n')

    print('> Autoaim Activated.\n')

    threads = []
    threads += [threading.Thread(target=app.read_image, args=[
        app_config,
        image_queue
    ])]
    threads += [threading.Thread(target=app.aim_enemy, args=[
        app_config,
        image_queue,
        packet_queue
    ])]
    if app_config['serial']:
        threads += [threading.Thread(target=app.send_packet, args=[
            app_config,
            packet_queue
        ])]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print('> Autoaim Deactivated.\n')
