import serial


class Keller:
    """
    Keller class for communication
    """
    _port = None
    _address = 0
    _echoOn = False
    _serial = None

    def __init__(self, address=250, port='', baundrate=9600):
        self._address = address
        self._port = port
        self._serial = serial.Serial(port=self._port)
        self._serial.baudrate = baundrate
        self._serial.timeout = 0.05

    def __del__(self):
        self._serial.close()

    def _CRC16(self, data: bytes):
        """"
        CRC-16-ModBus Algorithm
        :return: integer crc
        """
        data = bytearray(data)
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

    def _ArrayCrcKeller(self, data: bytes):
        return [i for i in self._CRC16(data).to_bytes(2, byteorder='big')]

    def _ArrayCrcModbus(self, data: bytes):
        return [i for i in reversed(self._ArrayCrcKeller(data))]

    def _SendRecive(self, frame: bytes):
        self._serial.write(frame)
        return self._serial.read(10)

    def _CheckCRC(self, data):
        frame = self._frame_to_array(data)
        if frame[1] > 16:
            crc_calc = self._ArrayCrcKeller(bytes(data[:-2]))
        else:
            crc_calc = self._ArrayCrcModbus(bytes(data[:-2]))

        if frame[1] > 0x80:  # todo: add error frame chcecked
            print('error frame')
        crc = self._frame_to_array(data[-2:])

        return True if crc == crc_calc else False

    def _frame_to_array(self, frame: bytes):
        return [i for i in frame]

    def ReadSerialNumber(self):
        frame = [self._address, 69]
        frame += self._ArrayCrcKeller(bytes(frame))
        recive = self._SendRecive(bytes(frame))
        if self._CheckCRC(recive):
            recive = self._frame_to_array(recive[2:6])
            recive.reverse()
            # SN = 256 3 * SN3 + 256 2 * SN2 + 256 * SN1 + SN0
            data = 0
            for i in range(0, 4):
                data += 256 ** i * recive[i]
            return data

    def EchoTest(self):
        frame = [self._address, 8]
        frame += self._ArrayCrcModbus(bytes(frame))
        pass
