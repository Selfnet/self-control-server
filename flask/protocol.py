# use construct to handle binary messages to and from the CAN Gateway
# message structure:


from construct import *

can_proto_ping = Struct('can_proto_ping',
                    OneOf(ULInt8('length'),range(9)),
                    MetaArray(lambda ctx: ctx['length'],
                        ULInt8('data'),
                    ),
                )

can_proto_text = Struct('can_proto_text',
                    OneOf(ULInt8('length'),range(9)),
                    MetaArray(lambda ctx: ctx['length'],
                        ULInt8('char'),
                    ),
                )

can_proto_sync = Struct('can_proto_sync',
                    OneOf(ULInt8('length'),[1]),
                    Enum(ULInt8('led_state'),
                        OFF = 0x00,
                        ON = 0x01,
                        TOGGLE = 0x02,
                    ),
                )

can_proto_acstate = Struct('can_proto_acstate',
                        OneOf(ULInt8('length'),[5]),
                        ULInt8('temp'),
                        Enum(Byte('mode'),
                            FREEZE = 0b01100000,
                            DRY= 0b10100000,
                            FAN = 0b00100000,
                            GEAR = 0b11000000,
                            AUTO = 0b11100000,
                            _default_ = 'UNKNOWN',
                        ),
                        Enum(Byte('fan'),
                            FAN_1 = 0b00000100,
                            FAN_2 = 0b00001000,
                            FAN_3 = 0b00000000,
                            FAN_AUTO = 0b00001100,
                            _default_ = 'UNKNOWN',
                        ),
                        Enum(Byte('swing'),
                            ON = 0b00000000,
                            OFF = 0b00000010,
                            _default_ = 'UNKNOWN',
                        ),
                        Enum(Byte('power'),
                            ON = 0b00000000,
                            OFF = 0b00010000,
                            _default_ = 'UNKNOWN',
                        ),
                )


can_proto_led = Struct('can_proto_led',
                                OneOf(ULInt8('length'),range(9)),
                                Embed(BitStruct('details',
                                    Enum(BitField('colormode',4),
                                        RGB = 0x0,
                                        HSV = 0x1,
                                        HSL = 0x2,
                                        _default_ = 'RGB',
                                    ),
                                    Array(lambda ctx: 4, Flag('leds')),
                                    ),
                                ),
                                Enum(Byte('mode'),
                                    MASTER = 0x01,
                                    COLOR = 0x02,
                                    FADE = 0x03,
                                    RANDOM = 0x04,
                                    AUTO = 0x05,
                                    STROBE = 0x06,
                                    CYCLE = 0x07,
                                    FADEMASTER = 0x08,
                                    POLICE = 0x09,
                                    _default_ = 'AUTO',
                                ),
                                Switch('modeselect', lambda ctx: ctx['mode'],
                                    {
                                        'MASTER': Embed(Struct('led',ULInt8('led'))),
                                        'COLOR': Embed( Struct('params',
                                                        ULInt16('time1'),
                                                        ULInt8('color1'),
                                                        ULInt8('color2'),
                                                        ULInt8('color3'),
                                                 ),),
                                        'FADE': Embed( Struct('params',
                                                        UBInt16('time1'),
                                                        ULInt8('color1'),
                                                        ULInt8('color2'),
                                                        ULInt8('color3'),
                                                 ),),
                                        'RANDOM': Embed(Struct('params',
                                                        ULInt16('time1'),
                                                        ULInt16('time2'),
                                                        ULInt8('color1'),
                                                        ULInt8('color2'),
                                                        ULInt8('color3'),
                                                  ),),
                                        'AUTO': Embed(Struct('params',
                                                        ULInt16('time1'),
                                                ),),
                                        'STROBE': Embed( Struct('params',
                                                        ULInt16('time1'),
                                                        ULInt8('color1'),
                                                        ULInt8('color2'),
                                                        ULInt8('color3'),
                                                        ULInt8('factor'),
                                                 ),),
                                        'CYCLE': Embed(Struct('params',ULInt16('time1'))),
                                        'FADEMASTER': Embed( Struct('params',
                                                        ULInt16('time1'),
                                                        ULInt8('led'),
                                                 ),),
                                        'POLICE': Embed(Struct('params',
                                                        ULInt16('time'),
                                                 ),),
                                    },
                                ),
                        )

can_proto_generic = Struct('can_proto_generic',
                    OneOf(ULInt8('length'),range(9)),
                    MetaArray(lambda ctx: ctx['length'],
                        ULInt8('data'),
                    ),
                )

can_msg = Struct('can_message',
            Embed(BitStruct('id',
                Padding(3),
                Enum(BitField('priority',2),
                    REGULAR = 0x2,
                    PROGRAM = 0x1,
                    NEGLECT = 0x3,
                    PRIORITY = 0x0,
                ),
                Enum(BitField('subnet',3),
                    ZERO = 0x0,
                    U6 = 0x2,
                    NOC = 0x4,
                    _default_ = 'UNKNOWN',
                ),
            ),),
            Enum(Byte('protocol'),
                PING = 0x08,
                PONG = 0x09,
                SYNC = 0x0A,
                AC = 0xA0,
                LED = 0xC0,
                TEXT = 0xD0,
                _default_ = 'UNKNOWN',
            ),
            Enum(Byte('receiver'),
                ADDR_GW = 32,
                ADDR_LED = 64,
                ADDR_BC = 255,
                _default_ = 'UNKNOWN',
            ),
            Enum(Byte('sender'),
                ADDR_GW = 32,
                ADDR_LED = 64,
                _default_ = 'UNKNOWN',
            ),
            Switch('data', lambda ctx: ctx['protocol'],
                {
                    'PING': Embed(can_proto_ping),
                    'PONG': Embed(can_proto_ping),
                    'SYNC': Embed(can_proto_sync),
                    'LED':  Embed(can_proto_led),
                    'TEXT': Embed(can_proto_text),
                    'UNKNOWN': Embed(can_proto_generic)
                }
            ),
        )

ping_msg = Struct('ping_msg',
            ULInt8('byte'),
        )

ascii_msg = Struct('ascii_msg',
                    ULInt32('length'),
                    String('content',lambda ctx: ctx.length),
            )

gw_msg = Struct('gw_msg',
                Enum(Byte('frametype'),
                    CAN_MSG = 0x15,
                    PING_MSG = 0x01,
                    ASCII_MSG = 0x20,
                    _default_ = 'UNKNOWN'
                ),
                Switch('content', lambda ctx: ctx['frametype'],
                    {
                        'CAN_MSG': Embed(can_msg),
                        'PING_MSG': Embed(ping_msg),
                        'ASCII_MSG': Embed(ascii_msg),
                    },
                    default = Pass
                ),
            )


ethernet_msg = Struct('msg',
                    OptionalGreedyRange(
                        Struct('sub_msgs',
                            ULInt16('ether_length'),
                            String('content',lambda ctx: ctx.ether_length)
                        )
                    )
                )

class PacketHandlerAdapter(Adapter):
    def _encode(self, msg, context):
        sub_msgs = []
        for container in msg:
            sub_msg_content = gw_msg.build(container)
            sub_msg_len = len(sub_msg_content)
            sub_container = Container(ether_length = sub_msg_len,
                                        content = sub_msg_content)
            sub_msgs.append(sub_container)
        return Container(sub_msgs = sub_msgs)

    def _decode(self, msg, context):
        sub_msgs = []
        for i,container in enumerate(msg.sub_msgs):
            sub_msg = gw_msg.parse(container.content)
            sub_msgs.append(sub_msg)
        return sub_msgs

def PacketHandler():
    return PacketHandlerAdapter(ethernet_msg)

def gotohex(string):
    hex = ''
    for c in string:
        hex += '\\x%02x' % ord(c)
    return hex

def main():

    gw_msg_ping = Container(frametype = 'PING_MSG',
                            byte = 0x08
                            )
    gw_msg_ascii = Container(frametype = 'ASCII_MSG',
                            length = 5,
                            content = 'abcde'
                            )
    gw_msg_can = Container(frametype = 'CAN_MSG',
                            priority = 'REGULAR',
                            subnet = 'NOC',
                            protocol = 'SYNC',
                            sender = 'ADDR_GW',
                            receiver = 'ADDR_BC',
                            length = 1,
                            led_state = 'TOGGLE'
                        )

    can_string = gw_msg.build(gw_msg_can)
    ascii_string = gw_msg.build(gw_msg_ascii)
    ping_string = gw_msg.build(gw_msg_ping)

    print 'Single msg strings (for comparison):\n'
    print 'ping (len \\x%02x): ' %len(ping_string) + gotohex(ping_string)
    print 'ascii(len \\x%02x): ' %len(ascii_string) + gotohex(ascii_string)
    print 'can  (len \\x%02x): ' %len(can_string) + gotohex(can_string)

    gw_msgs = [gw_msg_ping,gw_msg_ascii,gw_msg_can]
    send_string = PacketHandler().build(gw_msgs)
    print '\n\nSend-String for Ethernet (ping,ascii,can):\n'
    print gotohex(send_string)

    gw_msg_containers = PacketHandler().parse(send_string)
    print '\n\ngw_msgs as they fall out of PacketHandler:\n'
    print gw_msg_containers

    print '\n\nunpacked messages in pretty print:\n'
    for msg in gw_msg_containers:
        print '\n' + str(msg)

if __name__ == '__main__':
    main()
