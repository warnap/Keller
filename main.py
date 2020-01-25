from src.Keller import Keller

device1 = Keller(1, port='COM1', baundrate=115200)

print(device1.ReadSerialNumber())

print(device1.EchoTest())

device1.__del__()
