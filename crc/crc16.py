#!/usr/bin/env python
# -*- coding: utf-8 -*-

POLYNOMIAL = 0x1021
INITIAL_REMAINDER = 0xFFFF
FINAL_XOR_VALUE = 0x0000
WIDTH = 16
TOPBIT = (1 << (WIDTH - 1))
crcTable = {}


def crcInit():
    SHIFT = WIDTH - 8
    for step in range(0, 256):
        remainder = step << SHIFT
        for bit in range(8, 0, -1):
            if remainder & TOPBIT:
                remainder = ((remainder << 1) & 0xFFFF) ^ 0x1021
            else:
                remainder = remainder << 1
        crcTable[step] = remainder


def crcFast(message, nBytes):
    crcInit()
    remainder = 0xFFFF
    data = 0
    byte = 0
    while byte < nBytes:
        # data = ord(message[byte]) ^ (remainder >> (WIDTH - 8))
        data = message[byte] ^ (remainder >> (WIDTH - 8))
        remainder = crcTable[data] ^ ((remainder << 8) & 0xFFFF)
        byte = byte + 1
    return hex(remainder)[2:]
