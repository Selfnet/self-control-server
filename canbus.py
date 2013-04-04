#!/usr/bin/env python

from threading import Thread, Event
import errno
import logging
import socket
import struct

log = logging.getLogger(__name__)


class CANProtocol(object):
    protocol = {
            'setMaster':    (1, 'B'),     # master
            'setColorRGB':  (2, 'HBBB'),   # red, green, blue
            'fadeToColor':  (3, 'HBBB'),  # delay, red, green, blue
            'randomColor':  (4, 'H'),     # delay
            'randomFading': (5, 'H'),     # delay
            'strobe':       (6, 'HBBBB'),    # time total, col1, col2, col3, factor
            'cycle':        (7, 'H'),     # delay
            }

    def _handle(self, func, *led_args, **kwargs):
        format_can = 0x15
        can_sender = 0x20
        can_receiver = 0x40
        can_type = 0xc0
        can_flags = 0x00
        can_header = struct.pack('>5B', format_can, can_flags, can_type, can_receiver, can_sender)
        led_bitfield = kwargs['led'] if 'led' in kwargs else 0b1111
        led_command, led_args_format = self.protocol[func]
        can_payload = struct.pack('>BB' + led_args_format, led_bitfield, led_command, *led_args)
        can_payload_length = struct.pack('B', len(can_payload))
        return can_header + can_payload_length + can_payload

    def __getattr__(self, name):
        if name in self.protocol:
            return lambda *args, **kwargs: self._handle(name, *args, **kwargs)
        else:
            raise AttributeError

class CANCommander(object):
    ''' manages a socket to the Ethernet-to-CAN converter board and exposes methods from a CANProtocol instance '''

    def __init__(self, endpoint, timeout=1.0, handle_receive=None):
        self.handle_receive = handle_receive
        self.protocol = CANProtocol()
        self.should_stop = False
        self.connected = Event()
        self.conn = Thread(target=self._thread, args=(endpoint, timeout))
        self.conn.daemon = True

    def start(self):
        ''' blocks until a connection is established '''
        self.conn.start()
        self.connected.wait()

    def stop(self):
        ''' blocks until the socket thread quits '''
        self.should_stop = True
        self.conn.join()

    def _send(self, data):
        if self.connected.is_set():
            self.sock.send(data)
        else:
            log.warn('Not connected, message ignored!')

    def __getattr__(self, name):
        func = self.protocol.__getattr__(name)
        return lambda *args, **kwargs: self._send(func(*args, **kwargs))

    def _thread(self, endpoint, timeout):
        while not self.should_stop:
            self.connected.clear()
            try:
                try:
                    self.sock = socket.create_connection(endpoint, timeout)
                except socket.timeout:
                    log.warn('Timeout, retrying...')
                    continue
                log.info('Connection established')
                self.connected.set()
                while not self.should_stop:
                    try:
                        msg = self.sock.recv(4096)
                    except socket.timeout:
                        pass
                    else:
                        if self.handle_receive is not None:
                            self.handle_receive(msg)
            except socket.error as e:
                if e.errno != errno.ECONNRESET:
                    log.warn('socket error: ' + str(e))
