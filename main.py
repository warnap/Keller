from src.Keller import Keller
import time

device2 = Keller()

device1 = Keller(1, port='COM1', baundrate=11200)
#
# print('SN: {}'.format(device1.ReadSerialNumber()))
# print(device1)
# for i in range(1):
#     data = device1.ReadPressureAndTemperature()
#
#     print('Pressure is {} mbar. Temperature is {} C'.format(data.get('pressure'), data.get('temperature')))

print(device1.ReadPressure())
print(device1.ReadRegister())