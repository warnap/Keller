from src.Keller import Keller
import time

device1 = Keller(1, port='COM1', baundrate=115200)

print('SN: {}'.format(device1.ReadSerialNumber()))
print(device1)
for i in range(11):
    data = device1.ReadPressureAndTemperature()

    print('Pressure is {} mbar. Temperature is {} C'.format(data.get('pressure'), data.get('temperature')))
