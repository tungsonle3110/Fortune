from labjack import ljm
import numpy as np


class ACS723:
    def __init__(self, handle, FS_CURRENT, DATA_LEN_CURRENT):
        self.handle = handle
        self.scanRate = FS_CURRENT
        self.scansPerRead = DATA_LEN_CURRENT
        # self.ref = 2.4

        # Stream Configuration
        self.aScanListNames = ["AIN2"]  # Scan list names to stream
        self.numAddresses = len(self.aScanListNames)
        try:
            self.aScanList = ljm.namesToAddresses(self.numAddresses, self.aScanListNames)[0]
        except Exception:
            pass

        # self.set_ef_index(10)
        # self.configure_acs723(10)

    def get_values(self):
        """
        self.set_buffer_size()
        self.start_stream()
        try:
            ret = ljm.eStreamRead(self.handle)
            cur = ret[0]
        except ljm.LJMError:
            cur = None
        self.stop_stream()

        # Convert:
        # Spannung >> Strom  0.86V >> 1A bei 5V
        # Spannung >> Strom  0.53V >> 1A bei 3.3V
        cur = np.sqrt(np.sum(np.float32(cur) ** 2)) / self.scansPerRead
        cur = ((cur - 0.244) / 0.83) * 1.4 * 3
        return cur
        """

        # cur = ljm.eReadName(self.handle, "AIN2_EF_READ_A")
        # print(f"RMS Voltage: {cur}")
        # cur = ljm.eReadName(self.handle, "AIN2_EF_READ_B")
        # print(f"Peak-to-Peak Voltage: {cur}")
        # cur = ljm.eReadName(self.handle, "AIN2_EF_READ_C")
        # print(f"DC Offset Voltage (Average): {cur}")
        # cur = ljm.eReadName(self.handle, "AIN2_EF_READ_D")
        # print(f"Period (Seconds) {cur}")

        """
        try:
            ljm.eWriteName(self.handle, "AIN2_EF_CONFIG_A", 1000)
            ljm.eWriteName(self.handle, "AIN2_EF_CONFIG_B", 50)
            ljm.eWriteName(self.handle, "AIN2_EF_CONFIG_D", 10000)
            ljm.eWriteName(self.handle, "AIN2_EF_INDEX", 10)
            rms = ljm.eReadName(self.handle, "AIN2_EF_READ_A")
            cur = (rms - self.ref) / 0.53
            if cur < 0:
                cur = 0
            return cur
        except ljm.LJMError:
            pass
        """
        return 0

    def set_ef_index(self, index):
        # Set the AIN2_EF_INDEX to select an extended feature
        try:
            ljm.eWriteName(self.handle, "AIN2_EF_INDEX", index)
        except ljm.LJMError:
            pass

    def configure_acs723(self, index):
        # Number of Samples: The number of samples to be acquired
        try:
            ljm.eWriteName(self.handle, "AIN2_EF_CONFIG_A", self.scansPerRead)  # 100
        except ljm.LJMError:
            pass
        #  Scan Rate: The frequency at which samples will be collected
        try:
            ljm.eWriteName(self.handle, "AIN2_EF_CONFIG_D", self.scanRate)  # 1000
        except ljm.LJMError:
            pass
        if index == 11:
            # Hysteresis (RMS Auto only):
            # The smallest step (analog voltage in binary) that will trigger period detection when using RMS Auto.
            # Larger values will better reject noise.
            # Smaller values can increase the accuracy of the period calculation.
            try:
                ljm.eWriteName(self.handle, "AIN2_EF_CONFIG_B", self.scanRate)  # 100
            except ljm.LJMError:
                pass

    def set_buffer_size(self):
        try:
            ljm.eWriteName(self.handle, "STREAM_BUFFER_SIZE_BYTES", 4096)
        except ljm.LJMError:
            pass

    def start_stream(self):
        try:
            self.scanRate = ljm.eStreamStart(self.handle, self.scansPerRead, self.numAddresses, self.aScanList,
                                             self.scanRate)
        except ljm.LJMError:
            pass

    def stop_stream(self):
        try:
            ljm.eStreamStop(self.handle)
        except ljm.LJMError:
            pass
