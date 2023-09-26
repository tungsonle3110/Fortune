import ADXL343
import LIS3MDL
import BNO055
import ICS40300
import ACS723

from labjack import ljm
import numpy as np
from tkinter import *

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
import pandas as pd
import time
import datetime
import random
import threading


class LabJack:
    def __init__(self):
        self.handle = None
        self.info = None
        self.deviceType = None
        self.is_run = False
        self.subplot_count = 1
        self.data_set = 0
        self.is_first_start = True
        self.is_first_stop = False
        self.start_time = None
        self.stop_time = None
        self.scan_rate = None

        # Parameter
        self.DATA_LEN_I2C = int(200)  # Datenlänge der I2C Sensoren
        self.FS_ADC = int(100e3)  # Abtastrate Mikrofon + Ultraschall
        self.DATA_LEN_ADC = int(30e3)  # Datenlänge Mikrofon + Ultraschall
        self.FS_CURRENT = int(1e3)  # Abtastrate Strommessung
        self.DATA_LEN_CURRENT = int(100)  # Datenlänge Strommessung

        self.adxl343_acc_x = [None for _ in range(self.DATA_LEN_I2C)]
        self.adxl343_acc_y = [None for _ in range(self.DATA_LEN_I2C)]
        self.adxl343_acc_z = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_acc_x = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_acc_y = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_acc_z = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_mag_x = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_mag_y = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_mag_z = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_gyr_x = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_gyr_y = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_gyr_z = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_temp = [None for _ in range(self.DATA_LEN_I2C)]
        self.ics40300_mic = [None for _ in range(self.DATA_LEN_ADC)]
        self.acs723_cur = [None for _ in range(self.DATA_LEN_CURRENT)]

        self.d = {'adxl343_acc_x': [], 'adxl343_acc_y': [], 'adxl343_acc_z': [],
                  'bno055_acc_x': [], 'bno055_acc_y': [], 'bno055_acc_z': [],
                  'bno055_mag_x': [], 'bno055_mag_y': [], 'bno055_mag_z': [],
                  'bno055_gyr_x': [], 'bno055_gyr_y': [], 'bno055_gyr_z': [],
                  'ics40300_mic': [], 'acs723_cur': []}
        self.df = None

        self.status = "offline"  # for Demo / Test / GUI Programming

        self.open_labjack()
        self.get_handle_info()
        self.configure_i2c()
        self.set_i2c_speed()
        self.set_i2c_options()
        self.configure_ain()

        self.ADXL343 = ADXL343.ADXL343(self.handle)
        self.LIS3MDL = LIS3MDL.LIS3MDL(self.handle)
        self.BNO055 = BNO055.BNO055(self.handle)
        self.ICS40300 = ICS40300.ICS40300(self.handle, self.FS_ADC, self.DATA_LEN_ADC)
        self.ACS723 = ACS723.ACS723(self.handle, self.FS_CURRENT, self.DATA_LEN_CURRENT)

        self.root = Tk()

        # configure the root window
        self.root.title("Fortune AI UI")
        # self.root.geometry("1300x1000+250-1500")
        # self.root.geometry("1300x1000-2500+0")
        self.root.geometry("1300x1000+0+0")
        self.root.configure(background="#00967F")
        # self.root.attributes('-fullscreen', False)

        # control frame
        self.side_frame = Frame(self.root)
        self.side_frame.pack(side=LEFT, fill=BOTH, expand=0)

        # plot frame
        self.plot_frame = Frame(self.root)
        self.plot_frame.pack(side=LEFT, fill=BOTH, expand=1)

        self.fig = plt.Figure()
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        # self.fig.canvas.mpl_connect('key_press_event', key_press_handler)

        # Control:
        self.control = StringVar()
        self.control_frame = LabelFrame(self.side_frame, text="Control")
        self.control_frame.pack(fill=X, expand=0)
        self.mode_shift = IntVar()
        self.mode_scale = Scale(self.control_frame, variable=self.mode_shift, from_=0, to=1, label="plot",
                                length=50, sliderlength=25, orient=HORIZONTAL, showvalue=0, command=self.mode_change)
        self.mode_scale.pack(side=LEFT, fill=X, expand=0, padx=2, pady=2)
        self.start_stop_frame = Frame(self.control_frame)
        self.start_stop_frame.pack(fill=X, expand=0)
        self.start_button = Radiobutton(self.start_stop_frame, text="Start", variable=self.control, value="start",
                                        command=self.start, indicator=0)
        self.start_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.stop_button = Radiobutton(self.start_stop_frame, text="Stop", variable=self.control, value="stop",
                                       command=self.stop, indicator=0)
        self.stop_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.reconnect_reset_frame = Frame(self.control_frame)
        self.reconnect_reset_frame.pack(fill=X, expand=0)
        self.reconnect_button = Button(self.reconnect_reset_frame, text="Reconnect", command=self.reconnect_labjack)
        self.reconnect_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.clear_dataframe_button = Button(self.reconnect_reset_frame, text="reset value",
                                             command=self.clear_dataframe)
        self.clear_dataframe_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Record:
        self.record_frame = LabelFrame(self.side_frame, text="Record")
        self.record_frame.pack(fill=X, expand=0)
        self.data_format_check = [IntVar() for _ in range(0, 4)]
        self.data_format_frame = LabelFrame(self.record_frame, text="Data Format")
        self.data_format_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.pickle_checkbutton = Checkbutton(self.data_format_frame, text=".pkl", variable=self.data_format_check[0],
                                              offvalue=False, onvalue=True, indicator=2)
        self.pickle_checkbutton.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.pickle_checkbutton.select()
        self.csv_checkbutton = Checkbutton(self.data_format_frame, text=".csv", variable=self.data_format_check[1],
                                           offvalue=False, onvalue=True, indicator=2)
        self.csv_checkbutton.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.excel_checkbutton = Checkbutton(self.data_format_frame, text=".xlsx", variable=self.data_format_check[2],
                                             offvalue=False, onvalue=True, indicator=2)
        self.excel_checkbutton.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.hdf_checkbutton = Checkbutton(self.data_format_frame, text=".hdf", variable=self.data_format_check[3],
                                           offvalue=False, onvalue=True, indicator=2)
        self.hdf_checkbutton.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.case_name_check = IntVar()
        self.case_name_frame = LabelFrame(self.record_frame, text="Case")
        self.case_name_frame.pack(fill=X, expand=0, padx=2, pady=2)
        self.case_none_radiobutton = Radiobutton(self.case_name_frame, text="none", variable=self.case_name_check,
                                                 value=0)
        self.case_none_radiobutton.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.case_left_radiobutton = Radiobutton(self.case_name_frame, text="left", variable=self.case_name_check,
                                                 value=1)
        self.case_left_radiobutton.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.case_middle_radiobutton = Radiobutton(self.case_name_frame, text="middle", variable=self.case_name_check,
                                                   value=2)
        self.case_middle_radiobutton.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.case_right_radiobutton = Radiobutton(self.case_name_frame, text="right", variable=self.case_name_check,
                                                  value=3)
        self.case_right_radiobutton.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.save_frame = Frame(self.record_frame)
        self.save_frame.pack(fill=X, expand=0)
        self.save_button = Button(self.save_frame, text="Save", command=lambda: self.record())
        self.save_button.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)

        # Status:
        self.status_frame = LabelFrame(self.record_frame, text="Status")
        self.status_frame.pack(fill=X, expand=0)
        # Current
        self.lbl_strom_text = StringVar(value='Current (Mean): xA')
        self.lbl_strom_label = Label(self.status_frame, textvariable=self.lbl_strom_text)
        self.lbl_strom_label.pack(fill=X, expand=0)
        # Temperature
        self.lbl_temperature_text = StringVar(value='Temperature: x°C')
        self.lbl_temperature_label = Label(self.status_frame, textvariable=self.lbl_temperature_text)
        self.lbl_temperature_label.pack(fill=X, expand=0)
        # Data set:
        self.data_set_text = StringVar(value=f'Data set: {self.data_set}')
        self.data_set_label = Label(self.status_frame, textvariable=self.data_set_text)
        self.data_set_label.pack(fill=X, expand=0)
        # Recording start time
        self.start_time_text = StringVar(value=f'Start time: x')
        self.start_label = Label(self.status_frame, textvariable=self.start_time_text)
        self.start_label.pack(fill=X, expand=0)
        # Recording stop time
        self.stop_time_text = StringVar(value=f'Stop time: x')
        self.stop_time_label = Label(self.status_frame, textvariable=self.stop_time_text)
        self.stop_time_label.pack(fill=X, expand=0)
        # Recording time
        self.scan_time_text = StringVar(value=f'Scan time: x')
        self.scan_time_label = Label(self.status_frame, textvariable=self.scan_time_text)
        self.scan_time_label.pack(fill=X, expand=0)

        # Scan rate:
        self.scan_rate_text = StringVar(value=f'Time/Dataset (Mean): x')
        self.scan_rate_label = Label(self.status_frame, textvariable=self.scan_rate_text)
        self.scan_rate_label.pack(fill=X, expand=0)
        # Status
        self.status_text = StringVar(value=f'Status: {self.status}')
        self.status_label = Label(self.status_frame, textvariable=self.status_text)
        self.status_label.pack(fill=X, expand=0)

        # Welle: Accelerometer
        self.ax_acc_welle, self.lines_acc_welle = self.create_subplot(3)
        self.ax_acc_welle.set_xlim(0, self.DATA_LEN_I2C)
        self.ax_acc_welle.set_ylim(-4, 4)
        self.ax_acc_welle.set_xlabel('Sample', fontsize=10)
        self.ax_acc_welle.set_ylabel('Acceleration (shaft) in g', fontsize=10)
        self.ax_acc_welle.yaxis.set_label_position("left")
        self.ax_acc_welle.legend(['X', 'Y', 'Z'])

        # Motor: Accelerometer
        self.ax_acc_motor, self.lines_acc_motor, = self.create_subplot(3)
        self.ax_acc_motor.set_xlim(0, self.DATA_LEN_I2C)
        self.ax_acc_motor.set_ylim(-4, 4)
        self.ax_acc_motor.set_xlabel('Sample', fontsize=10)
        self.ax_acc_motor.set_ylabel('Acceleration (motor) in g', fontsize=10)
        self.ax_acc_motor.yaxis.set_label_position("left")
        self.ax_acc_motor.legend(['X', 'Y', 'Z'])

        # Motor: Magnetometer
        self.ax_mag_motor, self.lines_mag_motor = self.create_subplot(3)
        self.ax_mag_motor.set_xlim(0, self.DATA_LEN_I2C)
        self.ax_mag_motor.set_ylim(-8000, 8000)
        self.ax_mag_motor.set_xlabel('Sample', fontsize=10)
        self.ax_mag_motor.set_ylabel('Magnetic field (motor) in uT', fontsize=10)
        self.ax_mag_motor.yaxis.set_label_position("left")
        self.ax_mag_motor.legend(['X', 'Y', 'Z'])

        # Motor: Gyroscope
        self.ax_gyr_motor, self.lines_gyr_motor = self.create_subplot(3)
        self.ax_gyr_motor.set_xlim(0, self.DATA_LEN_I2C)
        self.ax_gyr_motor.set_ylim(-100, 100)
        self.ax_gyr_motor.set_xlabel('Sample', fontsize=10)
        self.ax_gyr_motor.set_ylabel('Angular velocity (motor) in °/s', fontsize=10)
        self.ax_gyr_motor.yaxis.set_label_position("left")
        self.ax_gyr_motor.legend(['X', 'Y', 'Z'])

        # Microphone
        self.ax_mikrofon, self.lines_mikrofon = self.create_subplot_mic(1)
        self.ax_mikrofon.set_ylim(-0, 5)
        self.ax_mikrofon.set_xlim(0, self.DATA_LEN_ADC)
        self.ax_mikrofon.set_xlabel('Sample', fontsize=10)
        self.ax_mikrofon.set_ylabel('Amplitude in V', fontsize=10)
        self.ax_mikrofon.yaxis.set_label_position("left")
        self.ax_mikrofon.legend(['Microphone'])

    def open_labjack(self):
        try:
            # Open first found LabJack
            self.handle = ljm.openS("ANY", "ANY", "ANY")  # Any device, Any connection, Any identifier
            # handle = ljm.openS("T7", "ANY", "ANY")  # T7 device, Any connection, Any identifier
            # handle = ljm.openS("T4", "ANY", "ANY")  # T4 device, Any connection, Any identifier
            # handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")
            # Any device, Any connection, Any identifier
            self.status = "online"
            try:
                self.status_text.set(f'Status: {self.status}')
            except AttributeError:
                # AttributeError: 'LabJack' object has no attribute 'status_text'
                pass
        except ljm.LJMError as e:
            # LJM library error code 1314 LJME_NO_DEVICES_FOUND
            self.status = "offline"
            print(f"Error: {e}\tPlease reconnect the device")
            print("Offline Modus")
            try:
                self.status_text.set(f'Status: {self.status}')
            except AttributeError:
                # AttributeError: 'LabJack' object has no attribute 'status_text'
                pass
        except Exception as e:
            # AttributeError: 'NoneType' object has no attribute 'LJM_OpenS'
            self.status = "offline"
            print(f"Error: {e}\tPlease install Labjack")
            print("Offline Modus")
            try:
                self.status_text.set(f'Status: {self.status}')
            except AttributeError:
                # AttributeError: 'LabJack' object has no attribute 'status_text'
                pass

    def reconnect_labjack(self):
        self.handle = None
        self.info = None
        self.deviceType = None
        ljm.closeAll()
        self.open_labjack()
        self.get_handle_info()
        self.set_i2c_speed()
        self.set_i2c_options()
        self.set_sensors()
        self.configure_ain()

    def get_handle_info(self):
        try:
            self.info = ljm.getHandleInfo(self.handle)
            print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
                  "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
                  (self.info[0], self.info[1], self.info[2], ljm.numberToIP(self.info[3]), self.info[4], self.info[5]))
            self.deviceType = self.info[0]
        except (ljm.LJMError, TypeError):
            pass
        except Exception:
            pass

    def configure_i2c(self):
        try:
            # For the T7 and other devices, using FIO0 and FIO1 for the SCL and SDA pins.
            ljm.eWriteName(self.handle, "I2C_SDA_DIONUM", 3)  # SDA pin number = 3 (FIO3)
            ljm.eWriteName(self.handle, "I2C_SCL_DIONUM", 2)  # SCL pin number = 2 (FIO2)
            # ljm.eWriteName(self.handle, "I2C_SDA_DIONUM", 1)  # SDA pin number = 1 (FIO1)
            # ljm.eWriteName(self.handle, "I2C_SCL_DIONUM", 0)  # SCL pin number = 0 (FIO0)
        except ljm.LJMError as e:
            pass
        except Exception:
            pass

    def set_i2c_speed(self):
        try:
            # Speed throttle is inversely proportional to clock frequency.
            # 0 = (400kHz) max
            # 65516 = (~100 kHz)
            ljm.eWriteName(self.handle, "I2C_SPEED_THROTTLE", 0)  # Speed throttle = 0 (400kHz) max
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_i2c_options(self):
        try:
            # Options bits:
            #     bit0: Reset the I2C bus.
            #     bit1: Restart w/o stop
            #     bit2: Disable clock stretching.
            ljm.eWriteName(self.handle, "I2C_OPTIONS", 0)  # Options = 0
        except ljm.LJMError:
            pass
        except Exception:
            pass

    def set_sensors(self):
        try:
            self.ADXL343.handle = self.handle
            self.ADXL343.set_adxl343()
            self.LIS3MDL.handle = self.handle
            self.LIS3MDL.set_lis3mdl()
            self.BNO055.handle = self.handle
            self.BNO055.set_bno055()
            self.ICS40300.handle = self.handle
            self.ACS723.handle = self.handle
        except AttributeError:
            pass

    def configure_ain(self):
        if self.deviceType == ljm.constants.dtT4:
            # LabJack T4 configuration

            # AIN0 and AIN1 ranges are +/-5 V, stream settling is 0 (default) and
            # stream resolution index is 0 (default).
            aNames = ["AIN0_RANGE", "AIN1_RANGE", "STREAM_SETTLING_US",
                      "STREAM_RESOLUTION_INDEX"]
            aValues = [5.0, 5.0, 0, 0]
        else:
            # LabJack T7 and other devices configuration

            # Ensure triggered stream is disabled.
            try:
                ljm.eWriteName(self.handle, "STREAM_TRIGGER_INDEX", 0)
            except ljm.LJMError:
                pass
            except Exception:
                pass

            # Enabling internally-clocked stream.
            try:
                ljm.eWriteName(self.handle, "STREAM_CLOCK_SOURCE", 0)
            except ljm.LJMError:
                pass
            except Exception:
                pass

            #   Negative channel = single ended (199)
            #   AIN0 and AIN2 Range: +/-5.0 V (5.0).
            #   Settling, in microseconds = Auto (0)
            #   Resolution index = Default (0)
            aNames = ["AIN_ALL_NEGATIVE_CH", "AIN0_RANGE", "AIN2_RANGE",
                      "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
            aValues = [ljm.constants.GND, 5.0, 5.0, 0, 0]
            # Write the analog inputs' negative channels (when applicable), ranges,
            # stream settling time and stream resolution configuration.
            numFrames = len(aNames)
            try:
                ljm.eWriteNames(self.handle, numFrames, aNames, aValues)
            except ljm.LJMError:
                pass
            except Exception:
                pass

    def create_subplot(self, axis):
        ax = self.fig.add_subplot(3, 2, self.subplot_count)
        lines = []
        for _ in np.arange(axis):
            lines.append(ax.plot([], [])[0])
        self.subplot_count += 1
        return ax, lines

    def create_subplot_mic(self, axis):
        ax = self.fig.add_subplot(3, 1, 3)
        lines = []
        for _ in np.arange(axis):
            lines.append(ax.plot([], [])[0])
        return ax, lines

    def mode_change(self, mode_shift):
        if mode_shift == "0":
            self.mode_scale["label"] = "plot"
        elif mode_shift == "1":
            self.mode_scale["label"] = "not plot"

    def draw(self):
        if self.is_run:
            self.canvas.draw()
            self.root.after(100, self.draw)

    def start(self):
        self.clear_dataframe_button["state"] = DISABLED
        self.save_button["state"] = DISABLED
        if self.is_first_start:
            self.is_first_start = False
            self.start_time = datetime.datetime.now()
            self.start_time_text.set(f'Start time: {self.start_time}')
        if not self.is_run:
            self.is_run = True
            self.is_first_stop = True
            if self.mode_shift.get() == 0:
                self.draw()
                threading.Thread(target=self.update_figures).start()
            elif self.mode_shift.get() == 1:
                threading.Thread(target=self.update_figures).start()

    def stop(self):
        self.clear_dataframe_button["state"] = NORMAL
        self.save_button["state"] = NORMAL
        if self.is_first_stop:
            self.is_first_stop = False
            self.stop_time = datetime.datetime.now()
            self.stop_time_text.set(f'Stop time: {self.stop_time}')
            try:
                self.scan_rate = (self.stop_time - self.start_time) / self.data_set
            except ZeroDivisionError:
                self.scan_rate = "x"
            self.scan_time_text.set(f'Scan time: {self.stop_time - self.start_time}')
            self.scan_rate_text.set(f'Time/Dataset (Mean): {self.scan_rate}')
        self.is_run = False
        self.canvas.draw()

    def update_figures(self):
        while self.is_run:
            self.get_sensors_data()

            # ADXL343 (Welle) Daten abfragen
            self.lines_acc_welle[0].set_data(range(self.DATA_LEN_I2C), self.adxl343_acc_x)
            self.lines_acc_welle[1].set_data(range(self.DATA_LEN_I2C), self.adxl343_acc_y)
            self.lines_acc_welle[2].set_data(range(self.DATA_LEN_I2C), self.adxl343_acc_z)
            # BNO055 - Accelerometer
            self.lines_acc_motor[0].set_data(range(self.DATA_LEN_I2C), self.bno055_acc_x)
            self.lines_acc_motor[1].set_data(range(self.DATA_LEN_I2C), self.bno055_acc_y)
            self.lines_acc_motor[2].set_data(range(self.DATA_LEN_I2C), self.bno055_acc_z)
            # BNO055 - Magnetometer
            self.lines_mag_motor[0].set_data(range(self.DATA_LEN_I2C), self.bno055_mag_x)
            self.lines_mag_motor[1].set_data(range(self.DATA_LEN_I2C), self.bno055_mag_y)
            self.lines_mag_motor[2].set_data(range(self.DATA_LEN_I2C), self.bno055_mag_z)
            # BNO055 - Gyroscope
            self.lines_gyr_motor[0].set_data(range(self.DATA_LEN_I2C), self.bno055_gyr_x)
            self.lines_gyr_motor[1].set_data(range(self.DATA_LEN_I2C), self.bno055_gyr_y)
            self.lines_gyr_motor[2].set_data(range(self.DATA_LEN_I2C), self.bno055_gyr_z)
            # ADC - Mikrofon
            self.lines_mikrofon[0].set_data(range(self.DATA_LEN_ADC), self.ics40300_mic)
            # ADC - Strom  # 100 Werte mit 1kHz samplen und Mittelwert ausrechnen
            self.lbl_strom_text.set('Current: {:.3f}A'.format(np.mean(self.acs723_cur)))
            # Temperature
            self.lbl_temperature_text.set('Temperature: {:.1f}°C'.format(np.mean(self.bno055_temp)))

            self.add_dataframe()
            self.clear_values()
            # Data set
            self.data_set_text.set(f'Data set: {self.data_set}')

    def get_sensors_data(self):
        if self.status == "online":
            self.ADXL343.set_i2c_slave_address()
            for i in range(self.DATA_LEN_I2C):
                self.adxl343_acc_x[i], self.adxl343_acc_y[i], self.adxl343_acc_z[i] = self.ADXL343.get_values()

            self.BNO055.set_i2c_slave_address()
            for i in range(self.DATA_LEN_I2C):
                self.bno055_acc_x[i], self.bno055_acc_y[i], self.bno055_acc_z[i], \
                self.bno055_mag_x[i], self.bno055_mag_y[i], self.bno055_mag_z[i], \
                self.bno055_gyr_x[i], self.bno055_gyr_y[i], self.bno055_gyr_z[i], \
                self.bno055_temp = self.BNO055.get_values()

            self.ics40300_mic = self.ICS40300.get_values()

            self.acs723_cur = self.ACS723.get_values()

        elif self.status == "offline":
            for i in range(self.DATA_LEN_I2C):
                self.adxl343_acc_x[i] = round(random.uniform(-2, 2), 3)
                self.adxl343_acc_y[i] = round(random.uniform(-2, 2), 3)
                self.adxl343_acc_z[i] = round(random.uniform(-2, 2), 3)
                self.bno055_acc_x[i] = round(random.uniform(-2, 2), 3)
                self.bno055_acc_y[i] = round(random.uniform(-2, 2), 3)
                self.bno055_acc_z[i] = round(random.uniform(-2, 2), 3)
                self.bno055_mag_x[i] = round(random.uniform(-4000, 4000), 3)
                self.bno055_mag_y[i] = round(random.uniform(-4000, 4000), 3)
                self.bno055_mag_z[i] = round(random.uniform(-4000, 4000), 3)
                self.bno055_gyr_x[i] = round(random.uniform(-2, 2), 3)
                self.bno055_gyr_y[i] = round(random.uniform(-2, 2), 3)
                self.bno055_gyr_z[i] = round(random.uniform(-2, 2), 3)
                self.bno055_temp = round(random.uniform(23, 26), 3)
            for i in range(self.DATA_LEN_ADC):
                self.ics40300_mic[i] = round(random.uniform(2.30, 2.50), 3)
            for i in range(self.DATA_LEN_CURRENT):
                self.acs723_cur[i] = round(random.uniform(2, 3))

    def add_dataframe(self):
        self.d["adxl343_acc_x"].append(self.adxl343_acc_x)
        self.d["adxl343_acc_y"].append(self.adxl343_acc_y)
        self.d["adxl343_acc_z"].append(self.adxl343_acc_z)
        self.d["bno055_acc_x"].append(self.bno055_acc_x)
        self.d["bno055_acc_y"].append(self.bno055_acc_y)
        self.d["bno055_acc_z"].append(self.bno055_acc_z)
        self.d["bno055_mag_x"].append(self.bno055_mag_x)
        self.d["bno055_mag_y"].append(self.bno055_mag_y)
        self.d["bno055_mag_z"].append(self.bno055_mag_z)
        self.d["bno055_gyr_x"].append(self.bno055_gyr_x)
        self.d["bno055_gyr_y"].append(self.bno055_gyr_y)
        self.d["bno055_gyr_z"].append(self.bno055_gyr_z)
        self.d["ics40300_mic"].append(self.ics40300_mic)
        self.d["acs723_cur"].append(self.acs723_cur)
        self.data_set += 1

    def record(self):
        current_time = time.strftime("%Y%m%d_%H%M%S")
        self.df = pd.DataFrame(data=self.d)
        print(self.d["adxl343_acc_x"][0])
        print(self.d["adxl343_acc_x"][1])
        print(self.d["adxl343_acc_x"][2])
        print(self.d["adxl343_acc_x"][3])
        print(self.df)
        print(f"Data set: {len(self.df)}")
        case_name = "none"
        if self.case_name_check.get() == 0:
            case_name = "none"
        elif self.case_name_check.get() == 1:
            case_name = "left"
        elif self.case_name_check.get() == 2:
            case_name = "middle"
        elif self.case_name_check.get() == 3:
            case_name = "right"
        try:
            if self.data_format_check[0].get() == 1:
                self.df.to_pickle(f"./Messungen/{current_time}_dataframe_{case_name}.pkl")
            if self.data_format_check[1].get() == 1:
                self.df.to_csv(f"./Messungen/{current_time}_dataframe_{case_name}.csv", index=True)
            if self.data_format_check[2].get() == 1:
                self.df.to_excel(f"./Messungen/{current_time}_dataframe_{case_name}.xlsx", index=True)
            if self.data_format_check[3].get() == 1:
                self.df.to_hdf(f"./Messungen/{current_time}_dataframe_{case_name}.h5", key="df", mode="w")
        except AttributeError:
            pass

    def clear_dataframe(self):
        self.d = {'adxl343_acc_x': [], 'adxl343_acc_y': [], 'adxl343_acc_z': [],
                  'bno055_acc_x': [], 'bno055_acc_y': [], 'bno055_acc_z': [],
                  'bno055_mag_x': [], 'bno055_mag_y': [], 'bno055_mag_z': [],
                  'bno055_gyr_x': [], 'bno055_gyr_y': [], 'bno055_gyr_z': [],
                  'ics40300_mic': [], 'acs723_cur': []}
        self.df = None
        self.data_set = 0
        self.data_set_text.set(f'Data set: {self.data_set}')
        self.is_first_start = True
        self.is_first_stop = False
        self.start_time = None
        self.start_time_text.set(f'Start time: x')
        self.stop_time = None
        self.stop_time_text.set(f'Stop time: x')
        self.scan_rate_text.set(f'Time/Dataset (Mean): x')

        # ADXL343 (Welle) Daten abfragen
        self.lines_acc_welle[0].set_data(None, None)
        self.lines_acc_welle[1].set_data(None, None)
        self.lines_acc_welle[2].set_data(None, None)
        # BNO055 - Accelerometer
        self.lines_acc_motor[0].set_data(None, None)
        self.lines_acc_motor[1].set_data(None, None)
        self.lines_acc_motor[2].set_data(None, None)
        # BNO055 - Magnetometer
        self.lines_mag_motor[0].set_data(None, None)
        self.lines_mag_motor[1].set_data(None, None)
        self.lines_mag_motor[2].set_data(None, None)
        # BNO055 - Gyroscope
        self.lines_gyr_motor[0].set_data(None, None)
        self.lines_gyr_motor[1].set_data(None, None)
        self.lines_gyr_motor[2].set_data(None, None)
        # ADC - Mikrofon
        self.lines_mikrofon[0].set_data(None, None)
        # ADC - Strom  # 100 Werte mit 1kHz samplen und Mittelwert ausrechnen
        self.lbl_strom_text.set('Current: xA')
        # Temperature
        self.lbl_temperature_text.set('Temperature: x°C')

        self.canvas.draw()

    def clear_values(self):
        self.adxl343_acc_x = [None for _ in range(self.DATA_LEN_I2C)]
        self.adxl343_acc_y = [None for _ in range(self.DATA_LEN_I2C)]
        self.adxl343_acc_z = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_acc_x = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_acc_y = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_acc_z = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_mag_x = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_mag_y = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_mag_z = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_gyr_x = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_gyr_y = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_gyr_z = [None for _ in range(self.DATA_LEN_I2C)]
        self.bno055_temp = [None for _ in range(self.DATA_LEN_I2C)]
        self.ics40300_mic = [None for _ in range(self.DATA_LEN_ADC)]
        self.acs723_cur = [None for _ in range(self.DATA_LEN_CURRENT)]


if __name__ == "__main__":
    main = LabJack()
    main.root.mainloop()
