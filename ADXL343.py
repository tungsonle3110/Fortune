from labjack import ljm
import numpy as np


class ADXL343:
    def __init__(self, handle):
        self.handle = handle
        self.set_adxl343()

    def set_adxl343(self):
        self.set_i2c_slave_address()
        self.set_power_ctl()
        self.set_data_format()

    def set_i2c_slave_address(self):
        try:
            ljm.eWriteName(self.handle, "I2C_SLAVE_ADDRESS", 0x53)  # Slave Address of the I2C chip = 83 (0x53)
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_power_ctl(self):
        try:
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 2)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 0)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 2, [0x2D, 0b00001000])  # Set bits in POWER_CTL
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_data_format(self):
        try:
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 2)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 0)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 2, [0x31, 0b00000001])  # Set bits in DATA_FORMAT
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def get_devid(self):
        try:
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 1)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 1)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x00])  # Set the TX Data = register of DIVID
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
            print(f"DIVID: {bin(ljm.eReadNameByteArray(self.handle, 'I2C_DATA_RX', 1)[0])}")  # 0b11100101
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def get_values(self):
        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 1)  # Set the number of bytes to transmit
        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 6)  # Set the number of bytes to receive

        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x32])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        data = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 6)

        # Convert
        # Note: g Kraft Umrechnung der Messwert in physikalische Größe
        acc_data_x = np.int16(data[1] * 256 + data[0]) * 4 / 512
        acc_data_y = np.int16(data[3] * 256 + data[2]) * 4 / 512
        acc_data_z = np.int16(data[5] * 256 + data[4]) * 4 / 512
        return acc_data_x, acc_data_y, acc_data_z
