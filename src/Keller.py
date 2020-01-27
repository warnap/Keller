import serial
import struct


class Keller:
    """
    Keller class for communication
    """
    _port = None
    _address = 0
    _echoOn = False
    _serial = None
    _deviceClass = None
    _deviceGroup = None
    _deviceYear = None
    _deviceWeek = None
    _deviceStatus = None
    _deviceFirmwareVersion = None

    def __init__(self, address=250, port=None, baundrate=9600):
        self._address = address
        self._port = port
        self._serial = serial.Serial(port=self._port)
        self._serial.baudrate = baundrate
        self._serial.timeout = 0.02
        self._EchoTest()
        self._InitDevice()

    def __str__(self):
        return 'Pressure sensor Addr:{} from {}'.format(self._address, self._port)

    def __del__(self):
        self._serial.close()

    def _CRC16(self, data):
        """"
        CRC-16-ModBus Algorithm
        :return: integer crc
        """
        data = bytearray(bytes(data))
        poly = 0xA001
        crc = 0xFFFF
        for b in data:
            crc ^= (0xFF & b)
            for _ in range(0, 8):
                if (crc & 0x0001):
                    crc = ((crc >> 1) & 0xFFFF) ^ poly
                else:
                    crc = ((crc >> 1) & 0xFFFF)
        return crc

    def _ArrayCrcKeller(self, data):
        return [i for i in self._CRC16(bytes(data)).to_bytes(2, byteorder='big')]

    def _ArrayCrcModbus(self, data):
        return [i for i in reversed(self._ArrayCrcKeller(bytes(data)))]

    def _SendReceive(self, frame, receiveLenght=10):
        # todo: Create function to check receive
        self._serial.write(bytes(frame))
        if self._echoOn:
            receive = self._frameToArray(self._serial.read(receiveLenght + len(frame)))
            receive = receive[len(frame):]
        else:
            receive = self._frameToArray(self._serial.read(receiveLenght))

        if receive is not None:
            if len(receive) == 5:
                if receive[1] > 0x80:
                    print('Error code = {}'.format(receive[2]))

        return receive

    def _CheckCRC(self, data):
        frame = self._frameToArray(data)
        crc = self._frameToArray(data[-2:])
        if frame[1] > 16:
            crc_calc = self._ArrayCrcKeller(data[:-2])
        else:
            crc_calc = self._ArrayCrcModbus(data[:-2])

        return True if crc == crc_calc else False

    def _frameToArray(self, frame):
        return [i for i in frame]

    def _InitDevice(self):
        frame = [self._address, 48]
        frame += self._ArrayCrcKeller(frame)
        receive = self._frameToArray(self._SendReceive(frame))

        print(receive)

    def ReadSerialNumber(self):
        frame = [self._address, 69]
        frame += self._ArrayCrcKeller(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            receive = self._frameToArray(receive[2:6])
            receive.reverse()
            # SN = 256 3 * SN3 + 256 2 * SN2 + 256 * SN1 + SN0
            data = 0
            for i in range(0, 4):
                data += 256 ** i * receive[i]
            return data

    def _EchoTest(self):
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
        frame = [self._address, 3, 0, 2, 0, 2]
        frame += self._ArrayCrcModbus(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            receive = self._frameToArray(receive[3:7])
            receive.reverse()
            data = struct.unpack('f', bytes(receive))
            return data[0]

    def ReadTemperature(self):
        frame = [self._address, 3, 0, 8, 0, 2]
        frame += self._ArrayCrcModbus(frame)
        receive = self._SendReceive(frame)
        if self._CheckCRC(receive):
            receive = self._frameToArray(receive[3:7])
            receive.reverse()
            data = struct.unpack('f', bytes(receive))
            return data[0]

    def ReadRegister(self):
        pass

    def WriteRegister(self):
        pass

