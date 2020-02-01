import serial
import struct
from .KellerExceptions import *


class _KellerBase:
    """
    Base class
    Keller communication protocol class for Series 30 of pressure sensors.
    """
    _port = None
    _address = 0
    _echoOn = False
    _serial = None
    _avaliableBaundrates = (9600, 115200)
    _deviceClass = None
    _deviceGroup = None
    _deviceYear = None
    _deviceWeek = None
    _deviceBuffer = None
    _deviceStatus = None
    _deviceFirmwareVersion = None

    def __init__(self, address=250, port=None, baundrate=9600):
        """
        Initialize Keller class
        :param address: 1 - 250
        :param port: Serial Port Comunication
        :param baundrate: 9600 115200
        """
        self._address = address
        self._port = port
        self._initSerialPort(baundrate=baundrate)
        self._EchoTest()
        self._initDevice()

    def __str__(self):
        return 'Pressure sensor ' \
               '\nAddr: {} port: {}' \
               '\nClass: {} Group: {} ' \
               '\nYear: {} Week: {}'.format(self._address,
                                            self._port,
                                            self._deviceClass,
                                            self._deviceGroup,
                                            self._deviceYear,
                                            self._deviceWeek)

    def __del__(self):
        pass

    def _initSerialPort(self, baundrate):
        self._serial = serial.Serial(port=self._port)
        self._serial.baudrate = baundrate
        self._serial.timeout = 0.05
        self._serial.parity = serial.PARITY_NONE
        self._serial.stopbits = serial.STOPBITS_ONE
        self._serial.bytesize = 8
        self._serial.close()
        if baundrate not in self._avaliableBaundrates:
            raise IllegalBaundrateValueException(
                'Illegal baundrate speed {} avaliable is only: {}'.format(baundrate, self._avaliableBaundrates))

    def _CRC16(self, frame):
        """"
        CRC-16-ModBus Algorithm
        :param frame: Data frame without crc code.
        For example frame[1, 3, 1, 0, 0, 4] frame with crc[1, 3, 1, 0, 0, 4, crcHI, crcLO]
        :return: Integer crc value
        """
        frame = bytearray(bytes(frame))
        poly = 0xA001
        crc = 0xFFFF
        for b in frame:
            crc ^= (0xFF & b)
            for _ in range(0, 8):
                if (crc & 0x0001):
                    crc = ((crc >> 1) & 0xFFFF) ^ poly
                else:
                    crc = ((crc >> 1) & 0xFFFF)
        return crc

    def _ArrayCrcKeller(self, data):
        """
        Converting crc data to array for Keller functions
        :param data: integer data to convert
        :return: Array of CRC16 [crcHI, crcLO]
        """
        return [i for i in self._CRC16(bytes(data)).to_bytes(2, byteorder='big')]

    def _ArrayCrcModbus(self, data):
        """
        Converting crc data to array for Modbus functions
        :param data: integer data to convert
        :return: Array of CRC16 [crcLO, crcHI]
        """
        return [i for i in reversed(self._ArrayCrcKeller(bytes(data)))]

    def _checkReceive(self, receive):

        if receive is not None:
            if len(receive) == 5:
                if receive[1] > 0x80:
                    address = receive[0]
                    function = receive[1]
                    # TODO: Add descriptions to all Exceptions using device address and function code.
                    error = receive[2]
                    if error == 1:
                        raise NonImplementedFunctionException()
                    if error == 2:
                        raise IllegalDataAddressException()
                    if error == 3:
                        raise IllegalDataValueException()
                    if error == 4:
                        raise DeviceSaveDataFailureException()
                    if error == 32:
                        raise DeviceIsNotInitializedException()
                    return False
                else:
                    return True

    def _SendReceive(self, frame, receiveLenght=20):
        """
        Internal function to send and get response from device.
        In this function:
            - serial port is opening
            - sending data frame
            - receiving data frame
            - closing serial port
        :param frame: data frame to send
        :param receiveLenght: how many bytes return received
        :return: received data frame
        """
        self._serial.open()
        self._serial.write(bytes(frame))
        if self._echoOn:
            receive = self._frameToArray(self._serial.read(receiveLenght + len(frame)))
            receive = receive[len(frame):]
        else:
            receive = self._frameToArray(self._serial.read(receiveLenght))

        self._serial.close()
        if not self._checkReceive(receive):
            return receive

    def _CheckCRC(self, frame):
        """
        Internal function checking CRC code from received data frame.
        :param frame: recieved data frame
        :return: boolean
        """
        frame = self._frameToArray(frame)
        crc = self._frameToArray(frame[-2:])
        if frame[1] > 16:
            crc_calc = self._ArrayCrcKeller(frame[:-2])
        else:
            crc_calc = self._ArrayCrcModbus(frame[:-2])
        return True if crc == crc_calc else False

    def _addCRC(self, frame):
        """
        Internal function checking function and add crc table to data frame.
        If number of function is greater than 16 it's Keller Function else it's Modbus Function
        :param frame: data frame without crc code
        :return: Full data frame to send
        """
        if frame[1] > 16:
            crc_calc = self._ArrayCrcKeller(frame)
        else:
            crc_calc = self._ArrayCrcModbus(frame)
        return frame + crc_calc

    def _frameToArray(self, frame):
        """
        Internal function converting data frame from bytes to Array
        :param frame: bytes(frame)
        :return: Array frame
        """
        return [i for i in frame]

    def _convertArrayToIEE754(self, data):
        """
        Internal function converting returned data from data frame to Format IEE754
        :param data: only 4 bytes data [B3, B2, B1, B0]
        :return: float value
        """
        # TODO: Add checking of +Inf and -Inf Exception
        data.reverse()
        data = struct.unpack('f', bytes(data))
        value = data[0]
        return value

    def _initDevice(self):
        """
        Internal function to initialize device.
        :return:
        """
        frame = [self._address, 48]
        frame = self._addCRC(frame)
        receive = self._frameToArray(self._SendReceive(frame))
        if self._CheckCRC(receive):
            self._deviceClass = receive[2]
            self._deviceGroup = receive[3]
            self._deviceYear = receive[4]
            self._deviceWeek = receive[5]
            self._deviceBuffer = receive[6]
            self._deviceStatus = receive[7]

    def _EchoTest(self):
        """
        Internal function for checking if EchoOFF is activated on device.
        :return: boolean
        """
        frame = [self._address, 8, 0, 0, 1, 1]
        frame = self._addCRC(frame)
        receive = self._frameToArray(self._SendReceive(frame, receiveLenght=len(frame) * 2))
        if len(receive) > len(frame):
            receive1 = receive[:len(frame)]
            receive2 = receive[len(frame):]
            if frame == receive1 == receive2:
                self._echoOn = True
        else:
            self._echoOn = False


class KellerMODBUS(_KellerBase):
    # Static MODBUS Address witch reg length [StAdd_HI, StAdd_LO, REG_HI, REG_LO]
    CH0_FLOAT = [0, 0, 0, 2]
    P1_FLOAT = [0, 2, 0, 2]
    P2_FLOAT = [0, 4, 0, 2]
    T_FLOAT = [0, 6, 0, 2]
    TOB1_FLOAT = [0, 8, 0, 2]
    TOB2_FLOAT = [0, 10, 0, 2]
    CH0_INT = [0, 16, 0, 1]  # Addr from 0x0010 one bait
    P1_INT = [0, 17, 0, 1]
    P2_INT = [0, 18, 0, 1]
    T_INT = [0, 19, 0, 1]
    TOB1_INT = [0, 20, 0, 1]
    TOB2_INT = [0, 21, 0, 1]

    UART = [2, 0, 0, 1]

    def ReadPressure(self):
        """
        Function return actual pressure value from sensor
        :return: float value
        """
        frame = [self._address, 3, 0, 2, 0, 2]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            value = self._convertArrayToIEE754(receive[3:-2])
            return value

    def ReadTemperature(self):
        """
        Function return actual pressure value from sensor
        :return: float value
        """
        frame = [self._address, 3, 0, 8, 0, 2]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            value = self._convertArrayToIEE754(receive[3:-2])
            return value

    def ReadSerialNumber(self):
        """
        Function return serial number of device.
        Calculating of the serial number using the formula:
        SN = 256 3 * SN3 + 256 2 * SN2 + 256 * SN1 + SN0
        :return: integer serial number
        """
        frame = [self._address, 3, 2, 2, 0, 2]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            receive = receive[3:-2]
            receive.reverse()
            data = 0
            for i in range(0, 4):
                data += 256 ** i * receive[i]
            return data

    def ReadPressureAndTemperature(self):
        """
        Function returned actual pressure and temperature values from sensor
        :return: dictionary float values Keys: pressure, temperature
        """
        frame = [self._address, 3, 1, 0, 0, 4]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            pressure = self._convertArrayToIEE754(receive[3:7])
            temperature = self._convertArrayToIEE754(receive[7:-2])
            return {
                'pressure': pressure,
                'temperature': temperature,
            }

    def ReadRegister(self, data):
        """
        stAddHI, stAddLO, regHI, regLO
        :param data: [StAdd_HI, StAdd_LO, REG_HI, REG_LO]
        :return: receive data from frame
        """
        frame = [self._address, 3] + data
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            receive = receive[3:-2]
            return receive

    def WriteSingleRegister(self):
        pass

    def WriteRegister(self):
        pass


class Keller(_KellerBase):
    CH0, P1, P2, T, TOB1, TOB2, LF, LF_raw = (0, 1, 2, 3, 4, 5, 10, 11)

    CFG_P, CFG_T, CFG_CH0, CNT_T, CNT_TCOMP = (0, 1, 2, 3, 4)
    FILTER, DAC, UART, FILTER_ORG, STAT = (7, 9, 10, 11, 12)
    DEV_ADDR, P_MODE, SPS, SDI_12 = (13, 14, 15, 20)
    LF_ON, LF_RANGE, LF_TEMP_COMP = (28, 31, 32)

    def ReadCoefficient(self):
        pass

    def WriteCoefficient(self):
        pass

    def ReadConfiguration(self, config=P1):
        frame = [self._address, 32, config]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame, 5)
        if self._CheckCRC(receive):
            data = receive[2]
            return bin(data)

    def WriteConfiguration(self):
        pass

    def InitialiseAndRelease(self):
        super()._initDevice()

    def WriteAndReadAddress(self):
        pass

    def ReadSerialNumber(self):
        """
        Function return serial number of device.
        Calculating of the serial number using the formula:
        SN = 256 3 * SN3 + 256 2 * SN2 + 256 * SN1 + SN0
        :return: integer serial number
        """
        frame = [self._address, 69]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            print(receive)
            receive = receive[2:-2]
            receive.reverse()
            data = 0
            for i in range(0, 4):
                data += 256 ** i * receive[i]
            return data

    def ReadValueOfChanelFloat(self):
        pass

    def ReadValueOfChannelInt(self):
        pass

    def SettingComand(self):
        pass

    def ReadPressure(self):
        """
        Function return actual pressure value from sensor
        :return: float value
        """
        frame = [self._address, 3, 0, 2, 0, 2]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            value = self._convertArrayToIEE754(receive[3:-2])
            return value

    def ReadTemperature(self):
        """
        Function return actual pressure value from sensor
        :return: float value
        """
        frame = [self._address, 3, 0, 8, 0, 2]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            value = self._convertArrayToIEE754(receive[3:-2])
            return value

    def ReadRegister(self):
        pass

    def WriteRegister(self):
        pass
