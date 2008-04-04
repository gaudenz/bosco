#/usr/bin/env python
#
#    Copyright (C) 2008  Gaudenz Steinlin <gaudenz@soziologie.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
sireader.py - Classes to read out si card data from BSM-7/8 stations.
"""

from serial import Serial
from datetime import datetime, timedelta, time
from binascii import hexlify

from course import SIStation

class SIReader(object):

    CRC_POLYNOM = 0x8005
    CRC_BITF    = 0x8000

    # Protocol characters
    STX           = '\x02'
    ETX           = '\x03'
    ACK           = '\x06'
    NAK           = '\x15'
    DLE           = '\x10'
    

    # Basic protocol commands
    BC_SET_MS     = '\x70'
    
    # Extended protocol commands
    C_GET_BACKUP  = '\x81'
    C_GET_SYS_VAL = '\x83'
    C_GET_SI5     = '\xB1'
    C_TRANS_REC   = '\xD3'
    C_GET_SI6     = '\xE1'
    C_SI5_DET     = '\xE5'
    C_SI6_DET     = '\xE6'
    C_SI_REM      = '\xE7'
    C_SI9_DET     = '\xE8'
    C_GET_SI9     = '\xEF'
    C_SET_MS      = '\xF0'
    C_ERASE_BDATA = '\xF5'
    C_SET_TIME    = '\xF6'
    C_GET_TIME    = '\xF7'
    C_SET_BAUD    = '\xFE'

    # Protocol Parameters
    P_MS_DIRECT   = '\x4D'
    P_MS_INDIRECT = '\x53'
    P_PROTO       = '\x74\x01'
    P_SI6_CB      = '\x08'

    # Backup memory record length
    REC_LEN       = 8

    # General card data structure values
    TIME_RESET    = '\xEE\xEE'
    
    # SI Card 5 data structure
    SI5_CNS       = 6
    SI5_CN1       = 4
    SI5_CN0       = 5
    SI5_ST        = 19
    SI5_FT        = 21
    SI5_CT        = 25
    SI5_RC        = 23
    SI5_1         = 32

    # SI Card 6 data structure
    SI6_CN        = 10
    SI6_ST        = 26
    SI6_FT        = 22
    SI6_CT        = 30
    SI6_LT        = 34
    SI6_RC        = 18
    SI6_1         = 128

    # SI Card 9 data structure
    SI9_CN        = 25
    SI9_ST        = 14
    SI9_FT        = 18
    SI9_CT        = 10
    SI9_RC        = 22
    SI9_1         = 56

    # punch trigger in control mode data structure
    T_OFFSET      = 8
    T_CN          = 0
    T_TIME        = 5

    # backup memory in control mode 
    BC_CN         = 3
    BC_TIME       = 8

    def __init__(self, port, debug = False):
        """Initializes communication with si station at port."""
        self._serial = Serial(port, baudrate = 38400, timeout = 5)
        # flush possibly available input
        self._serial.flushInput()
        
        self.station_code = None
        self._debug = debug

        try:
            # try at 38400 baud, extended protocol
            self._send_command(SIReader.C_SET_MS, SIReader.P_MS_DIRECT)
        except (SIReaderException, SIReaderTimeout):
            self._serial.baudrate = 4800
            try:
                self._send_command(SIReader.C_SET_MS, SIReader.P_MS_DIRECT)
            except SIReaderException:
                raise SIReaderException('This module only works with BSM7/8 stations')
        # Read protocol configuration
        ret = self._send_command(SIReader.C_GET_SYS_VAL, SIReader.P_PROTO)
        config_byte = ord(ret[1][1])
        self._proto_config = {}
        self._proto_config['ext_proto']  = config_byte & (1 << 0) != 0
        self._proto_config['auto_send']  = config_byte & (1 << 1) != 0
        self._proto_config['handshake']  = config_byte & (1 << 2) != 0
        self._proto_config['pw_access']  = config_byte & (1 << 4) != 0
        self._proto_config['punch_read'] = config_byte & (1 << 7) != 0

        if not self._proto_config['ext_proto']:
            raise SIReaderException('This module only supports stations in "Extended Protocol" mode.')

        self.port = port
        self.baudrate = self._serial.baudrate

    def __del__(self):
        self._serial.close()
        
    @staticmethod
    def _to_int(s):
        """Computes the integer value of a raw byte string."""
        value = 0
        for offset, c in enumerate(s[::-1]):
            value += ord(c) << offset*8
        return value

    @staticmethod
    def _to_str(i, len):
        """
        @param i:   Integer to convert into str
        @param len: Length of the return value. If i does not fit it's truncated.
        @return:    string representation of i (MSB first)
        """
        string = ''
        for offset in range(len-1, -1, -1):
            string += chr((i >> offset*8) & 0xFF)
        return string

    @staticmethod
    def _crc(s):
        """Compute the crc checksum of value. This implementation is
        a reimplementation of the Java function in the SI Programmers
        manual examples."""

        def twochars(s):
            """generator that split a string into parts of two chars"""
            if len(s) == 0:
                # immediately stop on empty string
                raise StopIteration
            
            # add 0 to the string and make it even length
            if len(s)%2 == 0:
                s += '\x00\x00'
            else:
                s += '\x00'
            for i in range(0, len(s), 2):
                yield s[i:i+2]

        if len(s) < 1:
            # return value for 1 or no data byte is 0
            return '\x00\x00'
        
        crc = SIReader._to_int(s[0:2])
        
        for c in twochars(s[2:]):
            val = SIReader._to_int(c)
            
            for j in range(16):
                if (crc & SIReader.CRC_BITF) != 0:
                    crc <<= 1
                
                    if (val & SIReader.CRC_BITF) != 0:
                        crc += 1 # rotate carry
                            
                    crc ^= SIReader.CRC_POLYNOM
                else:
                    crc <<= 1

                    if (val & SIReader.CRC_BITF) != 0:
                        crc += 1 # rotate carry
                        
                val <<= 1

        # truncate to 16 bit and convert to char
        crc &= 0xFFFF
        return chr(crc >> 8) + chr(crc & 0xFF)

    @staticmethod
    def _crc_check(s, crc):
        return SIReader._crc(s) == crc

    @staticmethod
    def _decode_cardnr(number):
        """Decodes a 4 byte cardnr to an int. SI-Card numbering is a bit odd:
           SI-Card 5:   byte 0:   always 0 (not stored on the card)
                        byte 1:   card series (stored on the card as CNS)
                        byte 2,3: card number
                        printed:  100'000*CNS + card number
                        nr range: 1-499'999 
           SI-Card 6/9: byte 0:   card series (apparently 0 on all currently sold cards)
                        byte 1-3: card number
                        printed:  only card number
                        nr range: SI6: 500'000-999'999, SI9: 1'000'000-1'999'999
           The card nr ranges guarantee that no ambigous values are possible
           (500'000 = 0x07A120 > 0x04FFFF -> 465535 (highest actually possible value on a SI5))   
        """
        
        if number[0] != '\x00':
            raise SIReaderException('Unknown card series')
        
        nr = SIReader._to_int(number[1:4])
        if nr < 500000:
            # SI5 card
            return ord(number[1])*100000 + SIReader._to_int(number[2:4])
        else:
            # SI6/9
            return nr

    @staticmethod
    def _decode_time(raw_time, reftime = None):
        """Decodes a raw time value read from an si card into a datetime object.
        The returned time is the nearest time matching the data before reftime."""

        if raw_time == SIReader.TIME_RESET:
            return None

        if reftime is None:
            reftime = datetime.now()

        #punchtime is in the range 0h-12h!
        punchtime = timedelta(seconds = SIReader._to_int(raw_time))
        ref_day = reftime.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        ref_hour = reftime - ref_day
        t_noon = timedelta(hours=12)

        if ref_hour < t_noon:
            # reference time is before noon
            if punchtime < ref_hour:
                # t is between 00:00 and t_ref
                return ref_day + punchtime
            else:
                # t is afternoon the day before
                return ref_day - t_noon + punchtime
        else:
            # reference is after noon
            if punchtime < ref_hour - t_noon:
                # t is between noon and t_ref
                return ref_day + t_noon + punchtime
            else:
                # t is in the late morning
                return ref_day + punchtime

    @staticmethod
    def _append_punch(list, station, timedata, reftime):
        time = SIReader._decode_time(timedata, reftime)
        if time is not None:
            list.append((station, time))
                
    @staticmethod
    def _decode_si5(data, reftime = None):
        """Decodes a data record read from an SI Card 5."""

        ret = {}
        ret['card_number'] = SIReader._decode_cardnr('\x00'
                                                     + data[SIReader.SI5_CNS]
                                                     + data[SIReader.SI5_CN1]
                                                     + data[SIReader.SI5_CN0])
        ret['punches'] = []
        SIReader._append_punch(ret['punches'],
                               SIStation.START,
                               data[SIReader.SI5_ST:SIReader.SI5_ST+2],
                               reftime)
        SIReader._append_punch(ret['punches'],
                               SIStation.FINISH,
                               data[SIReader.SI5_FT:SIReader.SI5_FT+2],
                               reftime)
        SIReader._append_punch(ret['punches'],
                               SIStation.CHECK,
                               data[SIReader.SI5_CT:SIReader.SI5_CT+2],
                               reftime)

        punch_count = ord(data[SIReader.SI5_RC]) - 1 # RC is the index of the next punch
        if punch_count > 30:
            # Only 30 punches with time available
            punch_count = 30
            
        p = i = 0
        while p < punch_count:
            if i % 16 == 0:
                # first byte of each block is reserved for punches 31-36
                i += 1
            SIReader._append_punch(ret['punches'],
                                   ord(data[SIReader.SI5_1 + i]),
                                   data[SIReader.SI5_1 + i + 1:SIReader.SI5_1 + i + 3],
                                   reftime)
            i += 3
            p += 1

        return ret
    
    @staticmethod
    def _decode_si6(data, reftime = None):
        """Decodes a data record read from an SI Card 6."""
        ret = {}
        ret['card_number'] = SIReader._to_int(data[SIReader.SI6_CN:SIReader.SI6_CN+4])

        ret['punches'] = []
        SIReader._append_punch(ret['punches'],
                               SIStation.START,
                               data[SIReader.SI5_ST:SIReader.SI6_ST+2],
                               reftime)
        SIReader._append_punch(ret['punches'],
                               SIStation.FINISH,
                               data[SIReader.SI5_FT:SIReader.SI6_FT+2],
                               reftime)
        SIReader._append_punch(ret['punches'],
                               SIStation.CHECK,
                               data[SIReader.SI5_CT:SIReader.SI6_CT+2],
                               reftime)
        SIReader._append_punch(ret['punches'],
                               SIStation.CHECK,
                               data[SIReader.SI5_CT:SIReader.SI6_LT+2],
                               reftime)

        punch_count = ord(data[SIReader.SI6_RC]) # RC is the punch count on the SI Card 6
        if punch_count > 64:
            # Currently SI Card 6* is not supported
            punch_count = 64
            
        for i in range(punch_count):
            SIReader._append_punch(ret['punches'],
                                   ord(data[SIReader.SI6_1 + i*4 + 1]),
                                   data[SIReader.SI6_1 + i*4 + 2:SIReader.SI6_1 + i*4 + 4],
                                   reftime)

        return ret
    
    @staticmethod
    def _decode_si9(data, reftime = None):
        """Decodes a data record read from an SI Card 9."""
        
        ret = {}
        ret['card_number'] = SIReader._to_int(data[SIReader.SI9_CN:SIReader.SI9_CN+3])

        ret['punches'] = []
        SIReader._append_punch(ret['punches'],
                               SIStation.START,
                               data[SIReader.SI5_ST:SIReader.SI9_ST+2],
                               reftime)
        SIReader._append_punch(ret['punches'],
                               SIStation.FINISH,
                               data[SIReader.SI5_FT:SIReader.SI9_FT+2],
                               reftime)
        SIReader._append_punch(ret['punches'],
                               SIStation.CHECK,
                               data[SIReader.SI5_CT:SIReader.SI9_CT+2],
                               reftime)

        punch_count = ord(data[SIReader.SI9_RC]) # RC is the punch count on the SI Card 6
        if punch_count > 50:
            raise SIReaderException('SI Card 9 with invalid punch count')
            
        for i in range(punch_count):
            SIReader._append_punch(ret['punches'],
                                   ord(data[SIReader.SI9_1 + i*4 + 1]),
                                   data[SIReader.SI9_1 + i*4 + 2:SIReader.SI9_1 + i*4 + 4],
                                   reftime)

        return ret

    def _send_command(self, command, parameters):
        if self._serial.inWaiting() != 0:
            raise SIReaderException('Input buffer must be empty before sending command. Currently %s bytes in the input buffer.' % self._serial.inWaiting())
        command_string = command + chr(len(parameters)) + parameters
        crc = SIReader._crc(command_string)
        self._serial.write(SIReader.STX + command_string + crc + SIReader.ETX)
        return self._read_command()

    def _read_command(self, timeout = None):


        if timeout != None:
            old_timeout = self._serial.timeout
            self._serial.timeout = timeout
        char = self._serial.read()
        if timeout != None:
            self._serial.timeout = old_timeout

        if char == '':
            raise SIReaderTimeout('No data available')
        elif char == SIReader.NAK:
            raise SIReaderException('Invalid command or parameter.')
        elif char != SIReader.STX:
            self._serial.flushInput()
            raise SIReaderException('Invalid start byte %s' % hex(ord(char))) 

        # Read command, length, data, crc, ETX
        cmd = self._serial.read()
        length = self._serial.read()
        station = self._serial.read(2)
        self.station_code = SIReader._to_int(station)
        data = self._serial.read(ord(length)-2)
        crc = self._serial.read(2)
        etx = self._serial.read()

        if etx != SIReader.ETX:
            raise SIReaderException('No ETX byte received.')
        if not SIReader._crc_check(cmd + length + station + data, crc):
            raise SIReaderException('CRC check failed')

        if self._debug:
            print "command '%s', data %s" % (hexlify(cmd), [hexlify(c) for c in data])

        return (cmd, data)

class SIReaderReadout(SIReader):
    """Class for 'classic' SI card readout. Reads out the whole card. If you don't know
    about other readout modes (control mode) you probably want this class."""

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        
        self.sicard = None
        self.cardtype = None

    def poll_sicard(self):
        """Polls for an SI-Card inserted or removed into the SI Station. Returns true on
        state changes and false otherwise. If other commands are received an Exception is
        raised."""
        try:
            c = self._read_command(timeout = 0)
        except SIReaderTimeout:
            return False
        
        if c[0] == SIReader.C_SI_REM:
            self.sicard = None
            self.cardtype = None
        elif c[0] == SIReader.C_SI5_DET:
            self.sicard = self._decode_cardnr(c[1])
            self.cardtype = 'SI5'
        elif c[0] == SIReader.C_SI6_DET:
            self.sicard = self._to_int(c[1])
            self.cardtype = 'SI6'
        elif c[0] == SIReader.C_SI9_DET:
            self.sicard = self._to_int(c[1][1:]) # SI 9 sends corrupt first byte (insignificant)
            self.cardtype = 'SI9'
        else:
            raise SIReaderException('Unexpected command %s received' % hex(ord(c[0])))

        return True

    def read_sicard(self):
        """Reads out the SI Card currently inserted into the station. The card must be
        detected with poll_sicard before."""
            
        if self.cardtype == 'SI5':
            return SIReader._decode_si5(self._send_command(SIReader.C_GET_SI5, '')[1])
        elif self.cardtype == 'SI6':
            raw_data  = self._send_command(SIReader.C_GET_SI6,
                                           SIReader.P_SI6_CB)[1][1:]
            raw_data += self._read_command()[1][1:]
            raw_data += self._read_command()[1][1:]
            return SIReader._decode_si6(raw_data)
        elif self.cardtype == 'SI9':
            raw_data  = self._send_command(SIReader.C_GET_SI9,
                                           '\x00')[1][1:]
            raw_data += self._send_command(SIReader.C_GET_SI9,
                                           '\x01')[1][1:]
            return SIReader._decode_si9(raw_data)
        else:
            raise SIReaderException('No card in the device.')
    
    def ack_sicard(self):
        """Sends an ACK signal to the SI Station. After receiving an ACK signal
        the station blinks and beeps to signal correct card readout."""
        self._serial.write(SIReader.ACK)


class SIReaderControl(SIReader):
    """Class for reading an SI Station configured as control in autosend mode."""

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        self._next_offset = None
        
    def poll_punch(self):
        """Polls for new punches.
        @retrun: list of (cardnr, punchtime) tuples, empty list if no new punches are available
        """

        punches = []
        while True:
            try:
                c = self._read_command(timeout = 0)
            except SIReaderTimeout:
                break 
        
            if c[0] == SIReader.C_TRANS_REC:
                cur_offset = SIReader._to_int(c[1][SIReader.T_OFFSET:SIReader.T_OFFSET+3])
                if self._next_offset is not None:
                    while self._next_offset < cur_offset:
                        # recover lost punches
                        punches.append(self._read_punch(self._next_offset))
                        self._next_offset += SIReader.REC_LEN

                self._next_offset = cur_offset + SIReader.REC_LEN
            punches.append( (self._decode_cardnr(c[1][SIReader.T_CN:SIReader.T_CN+4]), 
                             self._decode_time(c[1][SIReader.T_TIME:SIReader.T_TIME+2])) )
        else:
            raise SIReaderException('Unexpected command %s received' % hex(ord(c[0])))
        
        return punches
        
    def _read_punch(self, offset):
        """Reads a punch from the SI Stations backup memory.
        @param offset: Position in the backup memory to read
        @warining:     Only supports firmwares 5.55+ older firmwares have an incompatible record format!
        """
        c = self._send_command(SIReader.C_GET_BACKUP, SIReader._to_str(offset, 3)+chr(SIReader.REC_LEN))
        return (self._decode_cardnr('\x00'+c[1][SIReader.BC_CN:SIReader.BC_CN+3]), 
                self._decode_time(c[1][SIReader.BC_TIME:SIReader.BC_TIME+2]))

class SIReaderException(Exception):
    pass

class SIReaderTimeout(Exception):
    pass
        
