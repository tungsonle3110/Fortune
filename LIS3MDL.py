from labjack import ljm
import numpy as np


class LIS3MDL:
    def __init__(self, handle):
        self.handle = handle
        self.set_lis3mdl()

    def set_lis3mdl(self):
        self.set_i2c_slave_address()
        self.set_ctrl_reg1()
        self.set_ctrl_reg2()

    def set_i2c_slave_address(self):
        try:
            # Slave Address of the I2C chip
            # 0b0011110: SDO/SA1 is connected to voltage supply
            # 0b0011100: SDO/SA1 is connected to ground
            ljm.eWriteName(self.handle, "I2C_SLAVE_ADDRESS", 0b0011100)  # Slave Address of the I2C chip = 28 (0x1C)
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_ctrl_reg1(self):
        try:
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 2)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 0)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 2, [0x20, 0b10010000])  # Set bits in CTRL_REG1
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_ctrl_reg2(self):
        try:
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 2)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 0)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 2, [0x21, 0b00001000])  # Set bits in CTRL_REG2
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def get_who_am_i(self):
        try:
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 1)  # Set the number of bytes to transmit
            ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 1)  # Set the number of bytes to receive
            ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x0F])  # Set the TX Data = register of WHO_AM_I
            ljm.eWriteName(self.handle, "I2C_GO", 1)  # Do the I2C communications.
            print(f"WHO_AM_I: {bin(ljm.eReadNameByteArray(self.handle, 'I2C_DATA_RX', 1)[0])}")  # 0b11100101
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def get_values(self):  # need to be rechecked
        self.set_ctrl_reg2()
        # ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 1)  # Set the number of bytes to transmit
        # ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 8)  # Set the number of bytes to receive
        #
        # ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x28])
        # ljm.eWriteName(self.handle, "I2C_GO", 1)
        # data = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 8)
        #
        # # Convert
        # mag_data_x = np.int16(data[1] * 256 + data[0])
        # mag_data_y = np.int16(data[3] * 256 + data[2])
        # mag_data_z = np.int16(data[5] * 256 + data[4])
        #
        # temp_data = np.int16(data[7] * 256 + data[6])
        # return acc_data_x, acc_data_y, acc_data_z, temp_data

        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_TX", 1)  # Set the number of bytes to transmit
        ljm.eWriteName(self.handle, "I2C_NUM_BYTES_RX", 1)  # Set the number of bytes to receive

        # OUT_X_L
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x28])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        mag_data_x_l = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)

        # OUT_X_H
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x29])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        mag_data_x_h = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)

        # OUT_Y_L
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x2A])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        mag_data_y_l = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)

        # OUT_Y_H
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x2B])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        mag_data_y_h = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)

        # OUT_Z_L
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x2C])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        mag_data_z_l = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)

        # OUT_Z_H
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x2D])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        mag_data_z_h = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)

        # TEMP_OUT_L
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x2E])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        temp_data_l = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)
        # print(f"TEMP_OUT_L: {bin(temp_data_l[0])}")

        # TEMP_OUT_H
        ljm.eWriteNameByteArray(self.handle, "I2C_DATA_TX", 1, [0x2F])
        ljm.eWriteName(self.handle, "I2C_GO", 1)
        temp_data_h = ljm.eReadNameByteArray(self.handle, "I2C_DATA_RX", 1)
        # print(f"TEMP_OUT_H: {bin(temp_data_h[0])}")

        # Convert
        mag_data_x = np.int16(mag_data_x_h[0] * 256 + mag_data_x_l[0])
        mag_data_y = np.int16(mag_data_y_h[0] * 256 + mag_data_y_l[0])
        mag_data_z = np.int16(mag_data_z_h[0] * 256 + mag_data_z_l[0])
        temp_data = np.int16(temp_data_h[0] * 256 + temp_data_l[0])

        print(f"LIS3MDL Mag: x = {mag_data_x}, y = {mag_data_y}, z = {mag_data_z}, Temp: {temp_data}°C")
        # print(f"Temp_l = {temp_data_l} and Temp_h = {temp_data_h} Temp = {temp_data} \n")
        return mag_data_x, mag_data_y, mag_data_z, temp_data
