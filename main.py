from src.Keller import Keller
import datetime
device1 = Keller(1, port='COM1', baundrate=115200)

print(device1.ReadSerialNumber())
for i in range(101):
    print(datetime.datetime.now(), device1.ReadPressure())
    # print(device1.ReadTemperature())
    # print('Pressure {} Temperature {}'.format(device1.ReadPressure(), device1.ReadTemperature()))

print(device1._echoOn)


