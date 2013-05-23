# use construct to handle binary messages to and from the CAN Gateway
# message structure:


from construct import *


class PrintContext(Construct):
    def _parse(self,stream,context):
        print '\n' + self.name + 'parse'
        print context
        print "/" + self.name + '\n'
    def _build(self,obj,stream,context):
        print '\n' + self.name + 'build:'
        print context
        print "/" + self.name + '\n'

def can_proto_enum_macro(name):
    return Enum(
        Byte(name),
        PING = 0x08,
        PONG = 0x09,
        SYNC = 0x0A,
        TEXT = 0x10,
        AC = 0xA0,
        LED = 0xC0,
        LIGHT = 0xD0,
        _default_ = 'UNKNOWN'
    )

def can_address_enum_macro(name):
    return Enum(
        Byte(name),
        ADDR_GW0 = 0x20,
        ADDR_GW1 = 0x21,
        ADDR_LED = 0x40,
        ADDR_LIGHT = 0x80,
        ADDR_BC = 0xFF,
        _default_ = 'UNKNOWN'
    )

can_proto_ping = Struct('can_proto_ping',
    Range(0,8,UBInt8('data'))
)

can_proto_pong = Struct('can_proto_pong',
    UBInt16('can_time'),
    Range(0,6,UBInt8('data')),
)

can_proto_text = Struct('can_proto_text',
    Range(0,8,UBInt8('chars'))
)

can_proto_sync = Struct('can_proto_sync',
    Enum(ULInt8('led_state'),
        OFF = 0x00,
        ON = 0x01,
        TOGGLE = 0x02,
    ),
)

can_proto_light = Struct('can_proto_light',
    Byte('lights'),
    Enum(Byte('status'),
        OFF = 0,
        ON = 1,
        TOGGLE = 8,
        _default_ = 'UNKNOWN'
    )
)

can_proto_acstate = Struct('can_proto_acstate',
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

def build_mode(varname):
    return Enum(Byte(varname),
        MASTER = 0x01,
        COLOR = 0x02,
        FADE = 0x03,
        RANDOM = 0x04,
        AUTO = 0x05,
        STROBE = 0x06,
        CYCLE = 0x07,
        FADEMASTER = 0x08,
        POLICE = 0x09,
        GETCOLORRESPONSE = 0xFE,
        GETCOLOR = 0xFF,
        _default_ = 'AUTO',
    )

can_proto_led = Struct('can_proto_led',
    Embed(BitStruct('details',
        Enum(BitField('colormode',4),
            RGB = 0x0,
            HSV = 0x1,
            HSL = 0x2,
            _default_ = 'RGB',
        ),
        BitField('leds',4)
        ),
    ),
    build_mode('mode'),
    Switch('modeselect', lambda ctx: ctx['mode'], {
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
                        UBInt16('time1'),
                        UBInt8('color1'),
                        UBInt8('color2'),
                        UBInt8('color3'),
                        UBInt8('factor'),
                 ),),
        'CYCLE': Embed(Struct('params',ULInt16('time1'))),
        'FADEMASTER': Embed( Struct('params',
                        ULInt16('time1'),
                        ULInt8('led'),
                 ),),
        'POLICE': Embed(Struct('params',
                        ULInt16('time'),
                 ),),

        'GETCOLORRESPONSE': Embed( Struct('params',
                        build_mode('ledmode'),
                        ULInt8('color1'),
                        ULInt8('color2'),
                        ULInt8('color3'),
                 ),),
        'GETCOLOR': OptionalGreedyRange(UBInt8("foo")),
    },
    ),
)

can_proto_generic = Struct('can_proto_generic',
    Range(0,8,UBInt8('data'))
)

can_msg_data = Struct('can_msg_data',
    ULInt8('data_length'),
    Switch('data', lambda ctx: ctx._.protocol,{
            'PING': Embed(can_proto_ping),
            'PONG': Embed(can_proto_pong),
            'SYNC': Embed(can_proto_sync),
            'LED':  Embed(can_proto_led),
            'TEXT': Embed(can_proto_text),
            'LIGHT': Embed(can_proto_light),
            'UNKNOWN': Embed(can_proto_generic)
        }
    ),
)

can_msg_data_pre = Struct('can_msg_data_pre',
    can_proto_enum_macro('protocol'),
    can_msg_data
)


class CanDataAdapter(Adapter):
    def _decode(self, obj, context):
        return obj

    def _encode(self, obj, context):
        pre_inner_obj = Container(data_length=8)
        pre_inner_obj.update(obj)

        pre_obj = Container(
            protocol = context.protocol,
            can_msg_data = pre_inner_obj
        )

        pre_string = can_msg_data_pre.build(pre_obj)
        data_length = len(pre_string)-2 # protocol and length bytes

        data_length_con = Container(data_length = data_length)
        obj.update(data_length_con)
        return obj

can_msg_data_adapter = CanDataAdapter(can_msg_data)

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
    can_proto_enum_macro('protocol'),
    can_address_enum_macro('receiver'),
    can_address_enum_macro('sender'),
    can_msg_data_adapter
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
    Switch('content', lambda ctx: ctx['frametype'], {
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
    gw_msg_ascii = Container(
        frametype = 'ASCII_MSG',
        length = 5,
        content = 'abcde'
    )
    can_msg_data_container = Container(
        data = [1,2,3,4]
    )
    gw_msg_can = Container(
        frametype = 'CAN_MSG',
        priority = 'REGULAR',
        subnet = 'NOC',
        protocol = 'PING',
        sender = 'ADDR_GW',
        receiver = 'ADDR_BC',
        can_msg_data = can_msg_data_container
    )
    can_msg_data_container_light = Container(
        lights = 0b10101010,
        status = 'TOGGLE'
    )
    gw_msg_can_light = Container(
        frametype = 'CAN_MSG',
        priority = 'REGULAR',
        subnet = 'NOC',
        protocol = 'LIGHT',
        sender = 'ADDR_GW',
        receiver = 'ADDR_LIGHT',
        can_msg_data = can_msg_data_container_light
    )

    can_string = gw_msg.build(gw_msg_can)
    can_string_light = gw_msg.build(gw_msg_can_light)
    ascii_string = gw_msg.build(gw_msg_ascii)
    ping_string = gw_msg.build(gw_msg_ping)

    print 'Single msg strings (for comparison):\n'
    print 'ping (len \\x%02x): ' %len(ping_string) + gotohex(ping_string)
    print 'ascii(len \\x%02x): ' %len(ascii_string) + gotohex(ascii_string)
    print 'can  (len \\x%02x): ' %len(can_string) + gotohex(can_string)
    print 'canlight  (len \\x%02x): ' %len(can_string_light) + gotohex(can_string_light)

    gw_msgs = [gw_msg_ping,gw_msg_ascii,gw_msg_can,gw_msg_can_light]
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
