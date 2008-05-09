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
from serial.serialutil import SerialException
from datetime import datetime, timedelta, time
from binascii import hexlify
import os, re

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

    # SI Card data structures
    CARD          = {'SI5':{'CN2': 6,   # card number byte 2
                            'CN1': 4,   # card number byte 1
                            'CN0': 5,   # card number byte 0
                            'ST' : 19,  # start time
                            'FT' : 21,  # finish time
                            'CT' : 25,  # check time
                            'LT' : None,# clear time
                            'RC' : 23,  # punch counter
                            'P1' : 32,  # first punch
                            'PL' : 3,   # punch data length in bytes
                            'PM' : 30,  # punch maximum (punches 31-36 have no time)
                            'CN' : 0,   # control number offset in punch record
                            'PTH' :1,   # punchtime high byte offset in punch record
                            'PTL' :2,   # punchtime low byte offset in punch record
                            },
                     'SI6':{'CN2': 11,
                            'CN1': 12,
                            'CN0': 13,
                            'ST' : 26,
                            'FT' : 22,
                            'CT' : 20,
                            'LT' : 34,
                            'RC' : 18,
                            'P1' : 128,
                            'PL' : 4,
                            'PM' : 64,
                            'CN' : 1,
                            'PTH': 2,
                            'PTL': 3,
                            },
                     'SI9':{'CN2': 25,
                            'CN1': 26,
                            'CN0': 27,
                            'ST' : 14,
                            'FT' : 18,
                            'CT' : 10,
                            'LT' : None,
                            'RC' : 22,
                            'P1' : 56,
                            'PL' : 4,
                            'PM' : 50,
                            'CN' : 1,
                            'PTH': 2,
                            'PTL': 3,
                            },
                     }

    # punch trigger in control mode data structure
    T_OFFSET      = 8
    T_CN          = 0
    T_TIME        = 5

    # backup memory in control mode 
    BC_CN         = 3
    BC_TIME       = 8

    def __init__(self, port = None, debug = False):
        """Initializes communication with si station at port.
        @param port: Serial device for the connection if port is None it
                     scans all available ports and connects to the first
                     reader found
        """
        self._serial = None
        self._debug = debug
        errors = ''
        if port is not None:
            self._connect_reader(port)
            return
        else:
            scan_ports = [ os.path.join('/dev', f) for f in os.listdir('/dev') if
                           re.match('ttyS.*|ttyUSB.*', f) ]
            if len(scan_ports) == 0:
                errors = 'no serial ports found'
                
            for port in scan_ports:
                try:
                    self._connect_reader(port)
                    return
                except (SIReaderException, SIReaderTimeout), msg:
                    errors = '%sport: %s: %s\n' % (errors, port, msg)
                    pass

        raise SIReaderException('No SI Reader found. Possible reasons: %s' % errors)

    def _connect_reader(self, port):
        """Connect to SI Reader.
        @param port: serial port
        """
        
        try:
            self._serial = Serial(port, baudrate = 38400, timeout = 5)
        except (SerialException, OSError):
            raise SIReaderException("Could not open port '%s'" % port)
        
        # flush possibly available input
        self._serial.flushInput()
        
        self.station_code = None

        try:
            # try at 38400 baud, extended protocol
            self._send_command(SIReader.C_SET_MS, SIReader.P_MS_DIRECT)
        except (SIReaderException, SIReaderTimeout):
            try:
                self._serial.baudrate = 4800
            except (SerialException, OSError), msg:
                raise SIReaderException('Could not set port speed to 4800: %s' % msg)
            try:
                self._send_command(SIReader.C_SET_MS, SIReader.P_MS_DIRECT)
            except SIReaderException, msg:
                raise SIReaderException('This module only works with BSM7/8 stations: %s' % msg)
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
        if self._serial is not None:
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
            ret = SIReader._to_int(number[2:4])
            if ord(number[1]) == 1:
	        # Card series 1 does not have the 1 printed on the card
                return ret
            else:
                return ord(number[1])*100000 + ret
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
            # add two hours as a safety marging for cases where the
            # machine time runs a bit ahead of the stations time.
            reftime = datetime.now() + timedelta(hours=2)

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
    def _decode_carddata(data, card_type, reftime = None):
        """Decodes a data record read from an SI Card."""

        ret = {}
        card = SIReader.CARD[card_type]
        
        ret['card_number'] = SIReader._decode_cardnr('\x00'
                                                     + data[card['CN2']]
                                                     + data[card['CN1']]
                                                     + data[card['CN0']])
        ret['start'] = SIReader._decode_time(data[card['ST']:card['ST']+2],
                                             reftime)
        ret['finish'] = SIReader._decode_time(data[card['FT']:card['FT']+2],
                                             reftime)
        ret['check'] = SIReader._decode_time(data[card['CT']:card['CT']+2],
                                             reftime)
        if card['LT'] is not None:
            ret['clear'] = SIReader._decode_time(data[card['LT']:card['LT']+2],
                                                 reftime)
        else:
            ret['clear'] = None # SI 5 and 9 cards don't store the clear time

        punch_count = ord(data[card['RC']])
        if card_type == 'SI5':
            # RC is the index of the next punch on SI5
            punch_count -= 1
            
        if punch_count > card['PM']:
            punch_count = card['PM']
            
        ret['punches'] = []
        p = i = 0
        while p < punch_count:
            if card_type == 'SI5' and i % 16 == 0:
                # first byte of each block is reserved for punches 31-36
                i += 1
            SIReader._append_punch(ret['punches'],
                                   ord(data[card['P1'] + i + card['CN']]),
                                   data[card['P1'] + i + card['PTH']] +
                                   data[card['P1'] + i + card['PTL']],
                                   reftime)
            i += card['PL']
            p += 1
            
        # compatibility hack: add start, finish, clear and check as punches
        if ret['start'] is not None:
            ret['punches'].append((SIStation.START, ret['start']))
        if ret['finish'] is not None:
            ret['punches'].append((SIStation.FINISH, ret['finish']))
        if ret['check'] is not None:
            ret['punches'].append((SIStation.CHECK, ret['check']))
        if ret['clear'] is not None:
            ret['punches'].append((SIStation.CLEAR, ret['clear']))
        
        return ret

    def _send_command(self, command, parameters):
        try:
            if self._serial.inWaiting() != 0:
                raise SIReaderException('Input buffer must be empty before sending command. Currently %s bytes in the input buffer.' % self._serial.inWaiting())
            command_string = command + chr(len(parameters)) + parameters
            crc = SIReader._crc(command_string)
            self._serial.write(SIReader.STX + command_string + crc + SIReader.ETX)
        except (SerialException, OSError),  msg:
            raise SIReaderException('Could not send command: %s' % msg)
        
        return self._read_command()

    def _read_command(self, timeout = None):

        try:
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
                
        except (SerialException, OSError), msg:
            raise SIReaderException('Error reading command: %s' % msg)

        return (cmd, data)

class SIReaderReadout(SIReader):
    """Class for 'classic' SI card readout. Reads out the whole card. If you don't know
    about other readout modes (control mode) you probably want this class."""

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        
        self.sicard = None
        self.cardtype = None

    def poll_sicard(self):
        """Polls for an SI-Card inserted or removed into the SI Station.
        Returns true on state changes and false otherwise. If other commands
        are received an Exception is raised."""

        if self._serial.inWaiting() == 0:
            return False

        oldcard = self.sicard
        while self._serial.inWaiting() > 0:
            c = self._read_command(timeout = 0)
                    
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
                # SI 9 sends corrupt first byte (insignificant)
                self.sicard = self._to_int(c[1][1:]) 
                self.cardtype = 'SI9'
            else:
                raise SIReaderException('Unexpected command %s received' % hex(ord(c[0])))

        return not oldcard == self.sicard

    def read_sicard(self):
        """Reads out the SI Card currently inserted into the station. The card must be
        detected with poll_sicard before."""
            
        if self.cardtype == 'SI5':
            return SIReader._decode_carddata(self._send_command(SIReader.C_GET_SI5,
                                                                '')[1],
                                             self.cardtype)
        elif self.cardtype == 'SI6':
            raw_data  = self._send_command(SIReader.C_GET_SI6,
                                           SIReader.P_SI6_CB)[1][1:]
            raw_data += self._read_command()[1][1:]
            raw_data += self._read_command()[1][1:]
            return SIReader._decode_carddata(raw_data, self.cardtype)
        elif self.cardtype == 'SI9':
            raw_data  = self._send_command(SIReader.C_GET_SI9,
                                           '\x00')[1][1:]
            raw_data += self._send_command(SIReader.C_GET_SI9,
                                           '\x01')[1][1:]
            return SIReader._decode_carddata(raw_data, self.cardtype)
        else:
            raise SIReaderException('No card in the device.')
    
    def ack_sicard(self):
        """Sends an ACK signal to the SI Station. After receiving an ACK signal
        the station blinks and beeps to signal correct card readout."""
        try:
            self._serial.write(SIReader.ACK)
        except (SerialException, OSError), msg:
            raise SIReaderException('Could not send ACK: %s' % msg)


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
        
