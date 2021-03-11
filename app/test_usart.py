import autoaim
import serial
import struct
import time

# packet = bytes()
# packet += struct.pack('<I', val)
unpacker=autoaim.telegram.Unpacker()
with serial.Serial('COM3', 115200, timeout=0.1) as ser:
    t1 = time.time()
    count = 0
    fps=0
    while True:
        byte=ser.read(1)
        # print('Unpack: {:02X}'.format(byte))
        info=unpacker.send(int.from_bytes(byte, byteorder = 'little'))
        if info['state'] == 'EOF':
            data = info['packet'][7:-2]
            unpacked_data = struct.unpack('iiii', bytes(data))
            #fps
            count+=1
            if time.time()-t1>=1:
                t1 = time.time()
                fps = count
                count = 0
            print('id: 0x{:04X}'.format(info['id']), '; data: ', unpacked_data, '; fps: ', fps)