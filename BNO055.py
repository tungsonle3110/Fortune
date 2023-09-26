from labjack import ljm
import numpy as np


class BNO055:
    def __init__(self, handle):
        self.handle = handle
        self.set_bno055()

    def set_i2c_slave_address(self):
        try:
            # Slave Address of the I2C chip
            # 0b00101001 (0x29): COM3_state is HIGH
            # 0b00101000 (0x28): COM3_state is LOW
            ljm.eWriteName(self.handle, "I2C_SLAVE_ADDRESS", 0x28)  # Slave Address of the I2C chip = 40 (0x28)
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_unit_sel(self):
        try:
            # bit7: ORI_Android_Windows - 0: Windows orientation 1:Android orientation
            # bit5: TEMP_Unit - 0: Celsius  1: Fahrenheit
            # bit3: EUL_Unit - 0: Degrees  1: Radians
            # bit2: GYR_Unit - 0: dps (degrees per second / °/s)  1: rps (revolutions per second)
            # bit1: ACC_Unit - 0: m/s^2  1: mg
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 2)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 0)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 2, [0x3B, 0b00000001])  # Set bits in UNIT_SEL
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_opr_mode(self):
        try:
            # 0b00000111: Non-Fusion Mode AMG
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 2)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 0)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 2, [0x3D, 0b00000111])  # Set bits in OPR_MODE
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_temp_source(self):
        try:
            # 0b00000000: Source is Accelerometer
            # 0b00000001: Source is Gyroscope
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 2)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 0)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 2, [0x40, 0b00000000])  # Set bits in TEMP_SOURCE
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_bno055(self):
        self.set_i2c_slave_address()
        self.set_opr_mode()
        self.set_temp_source()

    def get_chip_id(self):
        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 1)  # Set the number of bytes to transmit
        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 1)  # Set the number of bytes to receive
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x00])  # Set the TX Data = register of CHIP_ID
        ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
        print(f"CHIP_ID: {hex(ljm.eReadNameByteArray(self.handle, 'I2C_DATA_RX', 1)[0])}")  # 0b11100101

    def get_values(self):
        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 1)  # Set the number of bytes to transmit
        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 9)  # Set the number of bytes to receive

        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x8])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        data = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 9)

        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x11])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        data += ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 9)

        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 1)  # Set the number of bytes to transmit
        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 1)  # Set the number of bytes to receive

        # Temperature
        # ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x34])
        # ljm.eWriteName(self.handle, "I2C_GO", 1)
        # data += ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)

        # Convert
        acc_data_x = np.int16(data[1] * 256 + data[0]) / 1000
        acc_data_y = np.int16(data[3] * 256 + data[2]) / 1000
        acc_data_z = np.int16(data[5] * 256 + data[4]) / 1000

        mag_data_x = np.int16(data[7] * 256 + data[6]) / 16
        mag_data_y = np.int16(data[9] * 256 + data[8]) / 16
        mag_data_z = np.int16(data[11] * 256 + data[10]) / 16

        gyr_data_x = np.int16(data[13] * 256 + data[12]) / 16
        gyr_data_y = np.int16(data[15] * 256 + data[14]) / 16
        gyr_data_z = np.int16(data[17] * 256 + data[16]) / 16

        # temp_data = np.int8(data[18])
        temp_data = 0

        # print(f"A: {acc_data_x}\t\t{acc_data_y}\t\t{acc_data_z}\t"
        #       f"{mag_data_x}\t\t{mag_data_y}\t\t{mag_data_z}\t"
        #       f"{gyr_data_x}\t\t{gyr_data_y}\t\t{gyr_data_z}\t"
        #       f"{temp_data}")
        return acc_data_x, acc_data_y, acc_data_z, mag_data_x, mag_data_y, mag_data_z, \
               gyr_data_x, gyr_data_y, gyr_data_z, temp_data

