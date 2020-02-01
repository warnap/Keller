import pytest
from src.Keller import _KellerBase
from src.KellerExceptions import *

"""
If you want to test you have to use devices:
1. USB <> RS485 converter ( K-114B from Keller druck  )
2. Pressure sensor ( PAA-33X ) 
"""

device = _KellerBase(250, port='COM1', baundrate=115200)


def test_baundrate():
    with pytest.raises(IllegalBaundrateValueException):
        assert device._initSerialPort(baundrate=9601)
        assert not device._initSerialPort(baundrate=9600)
        assert not device._initSerialPort(baundrate=115200)
        # assert _KellerBase(250, port='COM1', baundrate=9601)


# device = _KellerBase(250, port='COM1', baundrate=115200)


def test_CRC16():
    assert device._CRC16([1, 3, 1]) == 12513


def test_ArrayCrcKeller():
    """"test convert crc code to Keller type """
    assert device._ArrayCrcKeller(12513) == [159, 246]
    assert device._ArrayCrcKeller(1251) == [240, 90]
    assert device._ArrayCrcKeller(2513) == [163, 54]


def test_ArrayCrcModbus():
    """"test convert crc code to Modbus type """
    assert device._ArrayCrcModbus(12513) == [246, 159]
    assert device._ArrayCrcModbus(1251) == [90, 240]
    assert device._ArrayCrcModbus(2513) == [54, 163]


def test_CheckCRC():
    """test for check crc"""
    assert device._CheckCRC([1, 3, 1, 225, 48]) is True
    assert device._CheckCRC([1, 3, 1, 25, 48]) is False
    assert device._CheckCRC([1, 16, 1, 236, 0]) is True
    assert device._CheckCRC([1, 16, 1, 236, 1]) is False
    assert device._CheckCRC([1, 17, 1, 144, 237]) is True
    assert device._CheckCRC([1, 17, 1, 144, 37]) is False


def test_addCRC():
    """test for check added crc array"""
    assert device._addCRC([1, 3, 1]) == [1, 3, 1, 225, 48]
    assert device._addCRC([1, 16, 1]) == [1, 16, 1, 236, 0]
    assert device._addCRC([1, 17, 1]) == [1, 17, 1, 144, 237]


# b'\xfa0\x04C\xfa0\x05\x14\x0c\x1c\r\x01\xa3\xc8'

def test_frameToArray():
    pass


def test_convertArrayToIEE754():
    pass
