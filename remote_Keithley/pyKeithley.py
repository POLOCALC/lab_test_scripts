import pyvisa

class myKeithley:
	"""A class to control the Keithley 2231A_30_3 power supply.
	   This class allows to set the voltage on the three channels of the power supply and to switch it on and off.
	   The communication with the Keithley is managed by the pyvisa protocol.
	"""

	def __init__(self):
		self.rm = pyvisa.ResourceManager()
		self.PowerSupply = None
		self.Ch1_settings = dict.fromkeys(["Tension (V)", "Current Limitation (A)"])
		self.Ch2_settings = dict.fromkeys(["Tension (V)", "Current Limitation (A)"])
		self.Ch3_settings = dict.fromkeys(["Tension (V)", "Current Limitation (A)"])
		self.output_state = None
		return
		
	def print_settings(self):
		print(f"Current Channels settings: \n Ch1: {self.Ch1_settings} \n Ch2: {self.Ch2_settings} \n Ch3: {self.Ch3_settings} ")
		print(f"Current output state: {self.output_state}")
		
		
	def return_settings(self):
		return f"Current Channels settings: \n Ch1: {self.Ch1_settings} \n Ch2: {self.Ch2_settings} \n Ch3: {self.Ch3_settings}"
		
	def connect(self,COMport):
		"""Connect device using COM port
        Args:
            COMport (str): string containing COM port as listed by rm.list_resources(), e.g 'ASRL/dev/ttyUSB1::INSTR' if connected to the lower port of Rpy
        """
		print("connection to Keithley...")
		try:
			self.PowerSupply = self.rm.open_resource(COMport)
			self.PowerSupply.write("SYST:REM") # set the remote control of the power supply
			print(f"Keithley successfully connected") #: {self.powermeter.query('*IDN?')[:-1]}")
		except Exception as e:
			print(f"Connection failed: {e}")
		return
		
	def close(self):
		"""Close the connection with the power supply
		"""
		self.PowerSupply.write("SYST:LOC")
		self.PowerSupply.close()
		print("Keithley succesfully disconnected")
		return
		
	def switch_on_output(self):
		"""Switch on the output of the power supply
		"""
		current_key = "Current Limitation (A)"
		current_limitations = [self.Ch1_settings[current_key], self.Ch2_settings[current_key], self.Ch3_settings[current_key]]
		if(any(el is None for el in current_limitations)):
			print("You're not allowed to turn on the power supply without current limitations. Set the current limitation and try again...")
			return
		else:
			self.PowerSupply.write("OUTP 1")
			self.output_state = "ON"
			print(f"Output of the power supply: {self.output_state}")
			return
		
	def switch_off_output(self):
		"""Switch off the output of the power supply
		"""
		self.PowerSupply.write("OUTP 0")
		self.PowerSupply.output_state = "OFF"
		print(f"Output of the power supply: {self.PowerSupply.output_state}")
		return
	
	def set_single_tension(self,Ch_idx,tension_value,print_status=False):
		"""Set the tension of a single channel of the power supply
		   Args:
				Ch_idx (int): the index of the channel on which the tension value will be set:
						'1'->Channel 1
						'2'->Channel 2
						'3'->Channel 3
				tension_value (float): the tension value to be set on the channel selected
		"""
		self.PowerSupply.write(f"APPL CH{Ch_idx}, {tension_value}")
		print(f"Tension on Channel{Ch_idx} set to {tension_value}")
		if(Ch_idx == 1):
			self.Ch1_settings["Tension (V)"] = {tension_value}
		elif(Ch_idx == 2):
			self.Ch2_settings["Tension (V)"] = {tension_value}
		elif(Ch_idx == 3):
			self.Ch3_settings["Tension (V)"] = {tension_value}
		if print_status:
			print(f"Current Channels settings: \n {self.Ch1_settings} \n {self.Ch2_settings} \n {self.Ch3_settings} ")
		return
		
	def set_tensions(self,tension_CH1,tension_CH2,tension_CH3,print_status=False):
		"""Set the tension of all channels with a single function
		   Args:
				tension_CH* (float): the tension value to be set on the correspondent channel 
		"""
		self.PowerSupply.write(f"APP:VOLT {tension_CH1},{tension_CH2},{tension_CH3}")
		self.Ch1_settings["Tension (V)"] = {tension_CH1}
		self.Ch2_settings["Tension (V)"] = {tension_CH2}
		self.Ch3_settings["Tension (V)"] = {tension_CH3}
		print(f"Tension on Ch1 set to {tension_CH1} V")
		print(f"Tension on Ch2 set to {tension_CH2} V")
		print(f"Tension on Ch3 set to {tension_CH3} V")
		if print_status:
			print(f"Current Channels settings: \n {self.Ch1_settings} \n {self.Ch2_settings} \n {self.Ch3_settings} ")
		return
		
	def set_current_limitations(self,current_CH1,current_CH2,current_CH3,print_status=False):
		"""Set the current limitation of all channels with a single function
		   Args:
				current_CH* (float): the current value to be set on the correspondent channel 
		"""
		self.PowerSupply.write(f"APP:CURR {current_CH1},{current_CH2},{current_CH3}")
		self.Ch1_settings["Current Limitation (A)"] = {current_CH1}
		self.Ch2_settings["Current Limitation (A)"] = {current_CH2}
		self.Ch3_settings["Current Limitation (A)"] = {current_CH3}
		print(f"Current limitation on Ch1 set to {current_CH1} A")
		print(f"Current limitation on Ch2 set to {current_CH2} A")
		print(f"Current limitation on Ch3 set to {current_CH3} A")
		if print_status:
			print(f"Current Channels settings: \n {self.Ch1_settings} \n {self.Ch2_settings} \n {self.Ch3_settings} ")
		return
		
	""" COMMENTED SINCE NOT WORKING
	def get_current_tension(self):
		current_V = self.PowerSupply.write("FETC:VOLT?")
		print(current_V)
		return 
	"""
