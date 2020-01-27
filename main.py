from src.Keller import Keller

device1 = Keller(1, port='COM1', baundrate=115200)

print(device1.ReadSerialNumber())
# for i in range(11):
#     print(device1.ReadPressure())
#     print(device1.ReadTemperature())
#     # print('Pressure {} Temperature {}'.format(device1.ReadPressure(), device1.ReadTemperature()))
#
# print(device1.EchoTest())


