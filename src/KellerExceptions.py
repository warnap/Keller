class NonImplementedFunctionException(Exception):
    """ Keller Exception Code = 1 """
    pass


class IllegalDataAddressException(Exception):
    """ Keller Exception Code = 2 """
    pass


class IllegalDataValueException(Exception):
    """ Keller Exception Code = 3 """
    pass


class DeviceIsNotInitializedException(Exception):
    """ Keller Exception Code = 32 """
    pass


class DeviceSaveDataFailureException(Exception):
    pass


class IllegalBaundrateValueException(Exception):
    pass


class MessageLengthException(Exception):
    pass


class CRC16ValueException(Exception):
    pass
