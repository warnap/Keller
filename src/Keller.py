import serial
import struct
from .KellerExceptions import *


class Keller:
    """
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
        self._serial = serial.Serial(port=self._port)
        self._serial.baudrate = baundrate
        self._serial.timeout = 0.02
        self._serial.parity = serial.PARITY_NONE
        self._serial.stopbits = serial.STOPBITS_ONE
        self._serial.bytesize = 8
        if baundrate not in self._avaliableBaundrates:
            raise IllegalBaundrateValueException(
                'Illegal baundrae speed {} avaliable is only: {}'.format(baundrate, self._avaliableBaundrates))
        self._EchoTest()
        self._initDevice()

    def __str__(self):
        return 'Pressure sensor Addr:{} from {}'.format(self._address, self._port)

    def __del__(self):
        self._serial.close()

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

    def _SendReceive(self, frame, receiveLenght=20):
        # TODO: Create function to check receive
        self._serial.write(bytes(frame))
        if self._echoOn:
            receive = self._frameToArray(self._serial.read(receiveLenght + len(frame)))
            receive = receive[len(frame):]
        else:
            receive = self._frameToArray(self._serial.read(receiveLenght))

        if receive is not None:
            if len(receive) == 5:
                if receive[1] > 0x80:
                    if receive[2] == 2:
                        raise IllegalDataAddressException()
                    print('Error code = {}'.format(receive[2]))

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
        frame += self._ArrayCrcKeller(frame)
        receive = self._frameToArray(self._SendReceive(frame))
        # TODO: Finish function (_initDevice) to return value.

    def ReadSerialNumber(self):
        """
        Function return serial number of device.
        Calculating of the serial number using the formula:
        SN = 256 3 * SN3 + 256 2 * SN2 + 256 * SN1 + SN0
        :return: integer serial number
        """
        frame = [self._address, 69]
        frame += self._ArrayCrcKeller(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            receive = self._frameToArray(receive[2:6])
            receive.reverse()
            data = 0
            for i in range(0, 4):
                data += 256 ** i * receive[i]
            return data

    def _EchoTest(self):
        """
        Internal function for checking if EchoOFF is activated on device.
        :return: boolean
        """
        frame = [self._address, 8, 0, 0, 1, 1]
        frame += self._ArrayCrcModbus(frame)
        receive = self._frameToArray(self._SendReceive(frame, receiveLenght=len(frame) * 2))
        if len(receive) > len(frame):
            receive1 = receive[:len(frame)]
            receive2 = receive[len(frame):]
            if frame == receive1 == receive2:
                self._echoOn = True
        else:
            self._echoOn = False

    def ReadPressure(self):
        """
        Function return actual pressure value from sensor
        :return: float value
        """
        frame = [self._address, 3, 0, 2, 0, 2]
        frame = self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            value = self._convertArrayToIEE754(self._frameToArray(receive[3:7]))
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
            value = self._convertArrayToIEE754(self._frameToArray(receive[3:7]))
            return value

    def ReadPressureAndTemperature(self):
        """
        Function returned actual pressure and temperature values from sensor
        :return: dictionary float values Keys: pressure, temperature
        """
        frame = [self._address, 3, 1, 0, 0, 4]
        frame += self._addCRC(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            pressure = self._convertArrayToIEE754(self._frameToArray(receive[3:7]))
            temperature = self._convertArrayToIEE754(self._frameToArray(receive[7:11]))
            return {
                'pressure': pressure,
                'temperature': temperature,
            }

    def ReadRegister(self):
        stAddHI = 0x03
        stAddLO = 0x6A
        regHI = 0x00
        regLO = 0x01
        frame = [self._address, 3, stAddHI, stAddLO, regHI, regLO]
        frame = self._addCRC(frame)
        print(frame)
        receive = self._SendReceive(frame)
        print(receive)
        if self._CheckCRC(receive):
            return receive

    def WriteRegister(self):
        pass
