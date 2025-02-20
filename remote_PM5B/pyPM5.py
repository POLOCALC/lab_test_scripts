# -*- coding: utf-8 -*-

import copy
import numpy as np
import time
import struct

class PM5:
    """ A class that wraps the pyvisa object and allows for automatic power readings and
    range changes. The "powermeter" object contains the original pyvisa object that is used for
    communication. The read_power function basically sends a write/read command and interprets the returned information.
    """
    def __init__(self):
        import pyvisa 
        self.rm = pyvisa.ResourceManager()
        self.powermeter = None
        self.range_setting = None
        self.cal_factor = None
        self.cal_heater = None
        self.auto_range = None
        self.ranges = ["200uW", "2mW", "20mW", "200mW","200uW auto", "2mW auto", "20mW auto", "200mW auto"]
        self.hold_range = None
        self.range_hold_string = ["Off", "On"]
        self.auto_range_string = ["In auto range", "Not in auto range"]
        return
        
    def print_settings(self):
        """Print the current setting of the PM5B
        """
        print('PM5B current settings:')
        print(f'PM range settings: {self.range_setting}')
        print(f'PM cal factor: {self.cal_factor}')
        print(f"PM cal heater: {self.cal_heater}")
        print(f'PM auto range: {self.auto_range}')
        print(f'PM hold range: {self.hold_range}')
        
    def connect(self, COMport):
        """Connect device using COM port
        Args:
            COMport (str): string containing COM port as listed by rm.list_resources(), e.g ASRL16::INSTR
        """
        print('connection to power meter...')
        try:
            self.powermeter = self.rm.open_resource(COMport)
            print(f"Powermeter successfully connected") #: {self.powermeter.query('*IDN?')[:-1]}")
        except Exception as e:
            print(f"Connection failed: {e}")
        return

    def close(self):
        self.powermeter.close()
        print("Powermeter successfully closed")
        return

    def write(self, x):
        """ Allows access to native pyvisa object write function
        """
        self.powermeter.write(x)
        return

    def read(self, num_of_bytes):
        """ Allows access to native pyvisa object read_bytes function
        Args:
            num_of_bytes (int): number of bytes to be read by function
        """
        data = self.powermeter.read_bytes(num_of_bytes)
        return data

    def read_power(self):
        """ Returns the a single reading in units of watts, and updates
        range_setting and cal_factor properties.
        """
        ACK = 0x06  # acknowledged
        NAK = 0x015  # not acknowledged
        
        PM_range = self.range_setting
        
        # set the expected response parameters
        if(PM_range=='200mW'):
                Nbytes_to_read = 20
                buffer_cleaning = 20
                ACK_idx = 2
                range_bit = '100'
                wait_time = 0.1
                
        elif(PM_range=='20mW'):
                Nbytes_to_read = 20
                buffer_cleaning = 20
                ACK_idx = 2
                range_bit = '011'
                wait_time = 0.1
                
        elif(PM_range=='2mW'):
                Nbytes_to_read = 20
                buffer_cleaning = 20
                ACK_idx = 2
                range_bit = '010'
                wait_time = 0.3
                
        elif(PM_range=='200uW'):
                Nbytes_to_read = 20
                buffer_cleaning = 20
                ACK_idx = 2
                range_bit = '001'
                wait_time = 1.5
                
        buffer_str = self.powermeter.read_bytes(buffer_cleaning) # clear buffer
        self.powermeter.write("?D10000\r") # ask to read the power
        time.sleep(wait_time)
        out_string = self.powermeter.read_bytes(Nbytes_to_read) # read the answer from PM5
        
        
        # check the answer from the PM5 and identify the starting byte
        parse_check_byte = out_string[ACK_idx]
        if parse_check_byte != ACK:
            print("Write request parsed incorrectly")
        
        found_idx=False
        for i in range(len(out_string)):
                if(out_string[i]==68):
                        found_idx=True
                        start_msg=i

        if found_idx:
                data_string = copy.copy(out_string[start_msg:start_msg+6])
                        
                identifier_byte = data_string[0]
                LSB_byte = data_string[1]
                MSB_byte = data_string[2]
                status_byte_1 = data_string[3] # PM auto range
                status_byte_2 = data_string[4] # PM cal factor
                status_byte_3 = data_string[5] # PM power range
                
        else:
                print('Wrong comunication with PM5')
                return -np.inf
        
        status_byte_3_in_bits = format(status_byte_3, '#010b')[2:]
        range_binary = status_byte_3_in_bits[:3]
        
        if ((range_binary == '000') | (range_binary!=range_bit)):
            range_setting = 0
            print('wrong answer in range setting')
            return -np.inf
        elif range_binary == '001':
            range_setting = 200e-6
            range_index = 1
        elif range_binary == '010':
            range_setting = 2e-3
            range_index = 2
        elif range_binary == '011':
            range_setting = 20e-3
            range_index = 3
        else:
            range_setting = 200e-3
            range_index = 4
        #print(f"range binary = {range_binary}")
        #print(f"range setting = {range_setting}")
        self.range_setting = self.ranges[range_index-1]
        
        range_value = status_byte_1 & 0x03
        range_sets = {
                        1: 200e-6,# 200uW
                        2: 2e-3,  # 2mW
                        3: 20e-3, # 20mW
                        4: 200e-3# 200mW
                        
                      }
                      
        range_set = range_sets.get(range_value,0)
        
        auto_range = format(status_byte_1, '#010b')[2:][0]
        if auto_range == 1:
            self.auto_range = "In auto range"
        else:
            self.auto_range = "Not in auto range"
        
        # get cal factor from status byte 3 (bits 0-5)
        cal_factor = status_byte_3 & 0x3F
        if cal_factor > 9: # convert from 6-bit two's complement
                cal_factor -= 64
        self.cal_factor = cal_factor
        
        # convert LSB and MSB to signed 16-bit value using struct:
        count_value = struct.unpack('<h', bytes([LSB_byte,MSB_byte]))[0]
        
        # calculate reading:
        reading = count_value * 2.0 * range_set / 59576
        
        # apply cal factor if present:
        if cal_factor != 0:
                reading = reading * 10**(cal_factor/10)
        
        return reading
    
    def set_zero(self):
        """ Remotely zeros the powermeter
        """
        self.powermeter.write("!SZ0000\r")
        print("Power meter zeroed")
        return
    
    def set_range(self,range_index,range_hold = 1):
        """ Manually set the reading range, whilst the front panel is set to "Remote".
        Args:
            range_index (int) : index corresponding to the chosen power meter range
                1 : 200 microW
                2 : 2 mW
                3 : 20 mW
                4 : 200 mW
                5 : 200 uW auto
                6 : 2 mW auto
                7 : 20 mW auto
                8 : 200 mW auto
            range_hold (int): variable to choose whether to activate range hold mode, i.e to stop it
                automatically changing.
                0 : Range hold off
                1 : Range hold on
        """
        #ranges = ["200uW", "2mW", "20mW", "200mW","200uW auto", "2mW auto", "20mW auto", "200mW auto"]
        write_string = "!R" + str(range_index) + str(range_hold) + "000\r"
        self.powermeter.write(write_string)
        self.range_setting = self.ranges[range_index-1]
        self.auto_range = self.auto_range_string[range_hold]
        self.hold_range = self.range_hold_string[range_hold]
        print(f"Range set to {self.ranges[range_index-1]}, Range Hold = {self.range_hold_string[range_hold]}")
        return
        
    def set_cal_heater(self,cal_idx):
        """ Manually set the calibration heater, whilst the back knob is not set to "Off/Ext".
        Args:
            cal_index (int) : index corresponding to the chosen calibration
                0 : Calibration Heater OFF
                1 : Calibration Heater 100 µW
                2 : Calibration Heater 1 mW
                3 : Calibration Heater 10 mW
                4 : Calibration Heater 100 mW
        """
        cal_string = ['0','100uW','1mW','10mW','100mW']
        buffer_string = self.powermeter.read_bytes(30) #clear buffer
        write_string = "!C"+str(cal_idx)+"0000\r"
        self.powermeter.write(write_string)
        answer_string = self.powermeter.read_bytes(20)
        
        found_idx=False
        for i in range(len(answer_string)):
                if(answer_string[i]==6):
                        found_idx=True
        
        if found_idx:
                self.cal_heater = cal_string[cal_idx]
                print(f"Calibration heater set to: {self.cal_heater}")
        else:
                print(f"Error in setting the calibration heater.")
        
        return
        
