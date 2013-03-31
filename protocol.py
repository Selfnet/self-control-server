# use construct to handle binary messages to and from the CAN Gateway
# message structure:
# id(uint32),flags(uin8,rtr(:1),extended(:0)),length(uint8),data(uint8[length])
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
					Enum(ULInt8('ledState'),
						OFF = 0x00,
						ON = 0x01,
						_default_ = 'TOGGLE',
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


can_proto_led_payload = Struct('can_proto_led_payload',
				ULInt16('time'),
				ULInt8('color1'),
				ULInt8('color2'),
				ULInt8('color3'),
			)
			
test_payload = Struct('test_payload',
				ULInt8('time'),
			)


can_proto_led = Struct('can_proto_led',
                                OneOf(ULInt8('length'),[2,3,4,5,7,8]),
                        		Enum(Byte('mode'),
					                MASTER = 0x01,
					                COLOR = 0x02,
					                FADE = 0x03,
					                RANDOM = 0x04,
					                AUTO = 0x05,
					                STROBE = 0x06,
					                CIRCLE = 0x07,
					                FADEMASTER = 0x08,
					                POLICE = 0x09,
                                    _default_ = 'AUTO',
                                ),
				                Embed(BitStruct('details',
					                Array(lambda ctx: 4, Flag('leds')),
					                Enum(BitField('colormode',4),
						                RGB = 0x0,
						                HSV = 0x1,
						                HSL = 0x2,
						                _default_ = 'RGB',
					                ),
					                ),
				                ),
                                Switch('modeselect', lambda ctx: ctx['mode'],
					                {
						                'MASTER': Embed(Struct('led',ULInt8('led'))),
						                'COLOR': Embed( can_proto_led_payload ),
						                'FADE': Embed( can_proto_led_payload ),
						                'RANDOM': Embed(Struct('time',ULInt16('time'))),
						                'AUTO': Embed(Struct('time',ULInt16('time'))),
						                'STROBE': Embed( Struct('param',
								                                        Embed( can_proto_led_payload ),
								                                        ULInt8('factor'),
								                                    ),
							                            ),
						                'CIRCLE': Embed(Struct('time',ULInt16('time'))),
						                'FADEMASTER': Embed( Struct('fade',
									                                            ULInt16('time'),
									                                            ULInt8('led'),
									                                           ),
								                                ),
						                'POLICE': Embed(Struct('time',ULInt16('time'))),
					                },
					                #default = Pass
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
				Enum(BitField('service',2),
					REGULAR = 0x2,
					PROGRAM = 0x1,
					NEGLECT = 0x3,
					PRIORITY = 0x0,
				),
				Enum(BitField('subnet',3),
					U6 = 0x2,
					NOC = 0x4,
					_default_ = 'UNKNOWN',
				),
			),
			),
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
			ULInt8('char'),
		)
			
gw_msg = Struct('gw_msg',
				Enum(Byte('frametype'),
					CAN_MSG = 0x15,
					PING_MSG = 0x01,
					_default_ = 'UNKNOWN'
				),
				Switch('content', lambda ctx: ctx['frametype'],
					{
						'CAN_MSG': Embed(can_msg),
						'PING_MSG': Embed(ping_msg),
					},
					default = Pass
				),
			)
