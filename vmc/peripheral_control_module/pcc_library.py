# VRC Peripheral Python Library
# Written by Casey Hanner
from pickletools import int4
import time
from struct import pack
from typing import Any, List, Literal, Union

from loguru import logger
import serial


class VRC_Peripheral(object):
    def __init__(self, port: int, use_serial: bool = True) -> None:
        self.port = port

        self.PREAMBLE = (0x24, 0x50)

        self.HEADER_OUTGOING = (*self.PREAMBLE, 0x3C) #<
        self.HEADER_INCOMING = (*self.PREAMBLE, 0x3E) #>

        self.commands = {
            "SET_SERVO_OPEN_CLOSE": 0,
            "SET_SERVO_MIN": 1,
            "SET_SERVO_MAX": 2,
            "SET_SERVO_PCT": 3,
            "SET_BASE_COLOR": 4,
            "SET_TEMP_COLOR": 5,
            "SET_PIXEL_CYCLE" : 6,
            "SET_TRIGGER_SWITCH" : 7,
            "SET_SWITCH_ON" : 8,
            "SET_SWITCH_OFF" : 9,
            "SET_LASER_ON" : 10,
            "SET_LASER_OFF" : 11,
            "REQUEST_THERMAL_READING" : 12,
            "RESET_VRC_PERIPH": 13,
            "CHECK_SERVO_CONTROLLER": 14,
            "SEND_THERMAL_READING": 15,
        }

        self.use_serial = use_serial

        if self.use_serial:
            logger.debug("Opening serial port::::")
            self.ser = serial.Serial()
            self.ser.baudrate = 115200
            self.ser.port = self.port
            self.ser.timeout = 5
            self.ser.open()

        else:
            logger.debug("VRC_Peripheral: Serial Transmission is OFF")

        self.shutdown: bool = False


        # [$][P][>][LENGTH-HI][LENGTH-LOW][DATA][CRC]

    def parsein(self) -> List[int]:
        while self.ser.in_waiting > 0:
            logger.debug("data to be read parsein...")
            readdata = self.ser.read(2047)
            if (readdata[0]!=0x50): 
                logger.debug("Not correct start of instructions")
                logger.debug(readdata[1])

                return
            if (readdata[1]!=0x3E):
                logger.debug("Not correct direction")
                logger.debug(readdata[2])
                return
            code = readdata[2]
            if (code==self.commands["SEND_THERMAL_READING"]):
                byte_val = [readdata[3],readdata[4]]
                numrecs = int.from_bytes(byte_val, "big")
                logger.debug("datasize:")
                logger.debug(numrecs)
                data_val = readdata[6:numrecs]
                logger.debug(data_val) 
                return data_val
            else:
                logger.debug("not correct code")
                logger.debug(code)

    def run(self) -> None:
        logger.debug("Initiating RUN>>")

        while not self.shutdown:
            if self.use_serial:
                while self.ser.in_waiting > 0:
                  logger.debug("bytes")
                if (self.ser.in_waiting==0):
                    logger.debug("not bytes")
            time.sleep(0.01)

    def incoming(self) -> List[int]:
        logger.debug("checking for incoming")
        while self.ser.in_waiting > 0:
            logger.debug("data to be read...")
            readdata = self.ser.read(1)
            if (readdata[0]==0x24):
                return self.parsein()
            #else:
                #print(readdata, end="")
                #logger.debug(readdata)
            if (self.ser.in_waiting==0):
                logger.debug("not bytes")
            time.sleep(0.01)

    def set_base_color(self, wrgb: List[int]) -> None:
        # wrgb + code = 5
        if len(wrgb) != 4:
            wrgb = [0, 0, 0, 0]
            
        for i, color in enumerate(wrgb):
            if not isinstance(color, int) or color > 255 or color < 0:
                wrgb[i] = 0

        command = self.commands["SET_BASE_COLOR"]
        data = self._construct_payload(command, 1 + len(wrgb), wrgb)

        if self.use_serial is True:
            self.ser.write(data)
        else:
            logger.debug("VRC_Peripheral serial data: ")
            logger.debug(data)

    def set_temp_color(self, wrgb: List[int], time: float = 0.5) -> None:
        # wrgb + code = 5
        if len(wrgb) != 4:
            wrgb = [0, 0, 0, 0]

        for i, color in enumerate(wrgb):
            if not isinstance(color, int) or color > 255 or color < 0:
                wrgb[i] = 0

        command = self.commands["SET_TEMP_COLOR"]
        time_bytes = self.list_pack("<f", time)
        data = self._construct_payload(
            command, 1 + len(wrgb) + len(time_bytes), wrgb + time_bytes
        )

        if self.use_serial is True:
            self.ser.write(data)
        else:
            logger.debug("VRC_Peripheral serial data: ")
            logger.debug(data)

    def set_servo_open_close(self, servo: int, action: Literal["open", "close"]) -> None:
        valid_command = False

        command = self.commands["SET_SERVO_OPEN_CLOSE"]
        length = 3  # command + servo + action
        data = []

        # 128 is inflection point, over 128 == open; under 128 == close

        if action == "open":
            data = [servo, 150]
            valid_command = True
        elif action == "close":
            data = [servo, 100]
            valid_command = True

        if valid_command:
            if self.use_serial is True:
                self.ser.write(self._construct_payload(command, length, data))
            else:
                logger.debug("VRC_Peripheral serial data: ")
                logger.debug(data)

    def set_servo_min(self, servo: int, minimum: float) -> None:
        valid_command = False

        command = self.commands["SET_SERVO_MIN"]
        length = 3  # command + servo + min pwm
        data = []

        if isinstance(minimum, (float, int)) and minimum < 1000 and minimum > 0:
            valid_command = True
            data = [servo, minimum]

        if valid_command:
            if self.use_serial is True:
                self.ser.write(self._construct_payload(command, length, data))
            else:
                logger.debug("VRC_Peripheral serial data: ")
                logger.debug(data)

    def set_servo_max(self, servo: int, maximum: float) -> None:
        valid_command = False

        command = self.commands["SET_SERVO_MAX"]
        length = 3  # command + servo + min pwm
        data = []

        if isinstance(maximum, (float, int)) and maximum < 1000 and maximum > 0:
            valid_command = True
            data = [servo, maximum]

        if valid_command:
            if self.use_serial is True:
                self.ser.write(self._construct_payload(command, length, data))
            else:
                logger.debug("VRC_Peripheral serial data: ")
                logger.debug(data)

    def set_servo_pct(self, servo: int, pct: float) -> None:
        valid_command = False

        command = self.commands["SET_SERVO_PCT"]
        length = 3  # command + servo + percent
        data = []

        if isinstance(pct, (float, int)) and pct < 100 and pct > 0:
            valid_command = True
            data = [servo, int(pct)]

        if valid_command:
            if self.use_serial is True:
                self.ser.write(self._construct_payload(command, length, data))
            else:
                logger.debug("VRC_Peripheral serial data: ")
                logger.debug(data)

    def reset_vrc_peripheral(self) -> None:
        command = self.commands["RESET_VRC_PERIPH"]
        length = 1  # just the reset command

        if self.use_serial:

            self.ser.write(self._construct_payload(command, length))
            self.ser.close()
            # wait for the VRC_Periph to reboot
            time.sleep(5)

            # try to reconnect
            self.ser.open()
        else:
            logger.debug("VRC_Peripheral reset triggered (NO SERIAL)")

    def check_servo_controller(self) -> None:
        if self.use_serial:
            command = self.commands["CHECK_SERVO_CONTROLLER"]
            length = 1
            self.ser.write(self._construct_payload(command, length))

    def set_laser_on(self) -> None:
        if self.use_serial:
            command = self.commands["SET_LASER_ON"]
            length = 1
            self.ser.write(self._construct_payload(command, length))
        
    def request_thermal_reading(self) -> None:
        if self.use_serial:
            command = self.commands["REQUEST_THERMAL_READING"]
            length = 1
            self.ser.write(self._construct_payload(command, length))

    def set_laser_off(self) -> None:
        if self.use_serial:
            command = self.commands["SET_LASER_OFF"]
            length = 1
            self.ser.write(self._construct_payload(command, length))

    def set_pixel_cycle(self,pixel: int,waittime_ms: int) -> None:
        
        command = self.commands["SET_PIXEL_CYCLE"]
        length = 3  # command + pixel + waittime_ms
        data = []

        data = [waittime_ms, pixel]
        valid_command = True

        if valid_command:
            if self.use_serial is True:
                self.ser.write(self._construct_payload(command, length, data))
            else:
                logger.debug("VRC_Peripheral serial data: ")
                logger.debug(data)

    def set_trigger_switch(self,which_switch: int,howlong_ms: int) -> None:
        
        command = self.commands["SET_TRIGGER_SWITCH"]
        length = 3  # command + SWITCH + HOWLONG
        data = []

        data = [howlong_ms, which_switch]
        valid_command = True

        if valid_command:
            if self.use_serial is True:
                self.ser.write(self._construct_payload(command, length, data))
            else:
                logger.debug("VRC_Peripheral serial data: ")
                logger.debug(data)
                
    def set_switch_on(self,which_switch: int) -> None:
        
        command = self.commands["SET_SWITCH_ON"]
        length = 2  # command + SWITCH
        data = []

        data = [which_switch]
        valid_command = True

        if valid_command:
            if self.use_serial is True:
                self.ser.write(self._construct_payload(command, length, data))
            else:
                logger.debug("VRC_Peripheral serial data: ")
                logger.debug(data)

    def set_switch_off(self,which_switch: int) -> None:
        
        command = self.commands["SET_SWITCH_OFF"]
        length = 2  # command + SWITCH
        data = []

        data = [which_switch]
        valid_command = True

        if valid_command:
            if self.use_serial is True:
                self.ser.write(self._construct_payload(command, length, data))
            else:
                logger.debug("VRC_Peripheral serial data: ")
                logger.debug(data)



    def _construct_payload(self, code: int, size: int = 0, data: list = []):
        # [$][P][>][LENGTH-HI][LENGTH-LOW][DATA][CRC]
        payload = bytes()

        new_data = (
            ("<3b", self.HEADER_OUTGOING),
            (">H", [size]),
            ("<B", [code]),
            ("<%dB" % len(data), data),
        )

        for section in new_data:
            payload += pack(section[0], *section[1])

        crc = self.calc_crc(payload, len(payload))

        payload += pack("<B", crc)

        return payload

    def list_pack(self, bit_format: Union[str, bytes], value: Any) -> List[int]:
        bytez = pack(bit_format, value)

        return [byte for byte in bytez]

    def crc8_dvb_s2(self, crc, a):
        # https://stackoverflow.com/a/52997726
        crc ^= a
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0xD5) % 256
            else:
                crc = (crc << 1) % 256
        return crc

    def calc_crc(self, string: Union[str, bytes], length: int):
        crc = 0
        for i in range(length):
            crc = self.crc8_dvb_s2(crc, string[i])
        return crc
