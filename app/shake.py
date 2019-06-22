import autoaim
import cv2

seq = 0


def rotate(degree):
    #seq = (seq+1) % 256
    # packet = autoaim.telegram.pack(0x0401, [degree/20.0, 0])
    packet = autoaim.telegram.pack(
        0x0401, [0.0, 0.0, bytes([0])])
    autoaim.telegram.send(packet)
    cv2.waitKey(5)


while True:
    amplitude = 30
    for i in range(0, amplitude, 1):
        rotate(i)
    for i in range(amplitude, -1*amplitude, -1):
        rotate(i)
    for i in range(-1*amplitude, 0, 1):
        rotate(i)
