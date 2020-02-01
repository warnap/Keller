from src.Keller import Keller, KellerMODBUS
import csv
import time
import datetime

HEADER = ['time', 'datetime', 'pressure', 'temperature']
device1 = Keller(250, port='COM1', baundrate=115200)
device2 = Keller(1, port='COM1', baundrate=115200)


print(device1.ReadSerialNumber())
print(device1)
print(device2)
# print(device1.ReadConfiguration(Keller.CFG_P))
# print(device1.ReadConfiguration(Keller.CFG_T))
# print(device1.ReadConfiguration(Keller.CFG_CH0))
# print(device1.ReadConfiguration(Keller.FILTER))


# print(device2.ReadRegister(KellerMODBUS.UART))
# print(device2.ReadSerialNumber())

# with open('datas.csv', 'w', newline='') as csvfile:
#     csv_writer = csv.writer(csvfile)
#     csv_writer.writerow(HEADER)
#
# print(device1.ReadTemperature())

#
# while True:
#     data = device1.ReadPressureAndTemperature()
#     with open('datas.csv', 'a', newline='') as csvfile:
#         csv_writer = csv.writer(csvfile)
#         csv_writer.writerow([time.time(),
#                              datetime.datetime.now(),
#                              data.get('pressure'),
#                              data.get('temperature'), ])


# print('SN: {}'.format(device1.ReadSerialNumber()))
# print(device1)
# while True:
#     data = device1.ReadPressureAndTemperature()
#
#     print('Pressure is {} mbar. Temperature is {} C'.format(data.get('pressure'), data.get('temperature')))
#
# print(device1.ReadPressure())
# # print(device1.ReadRegister())
