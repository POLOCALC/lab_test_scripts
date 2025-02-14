import argparse
import sys
import time
import pyvisa
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, "/home/polocalc/Documents/lab_test_scripts/remote_Keithley") # add the path for the Keithley script
sys.path.insert(0, "/home/polocalc/Documents/lab_test_scripts/remote_PM5B") # add the path for the PM5B script
sys.path.insert(0, "/home/polocalc/Documents/porter/porter") # add the path for the valon

from pyKeithley import myKeithley
from pyPM5 import PM5
from valon import Valon

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-V", "--tension-res", help="Tension resolution (V)", type=float, default=0.1)
	parser.add_argument("-f", "--valon-freq", help="Ouput frequency of the Valon (GHz)",type=float,default=93)
	args = parser.parse_args()
	
	# define max and min values for the tension applied to the multiplier attenuator and the step:
	min_tens = 0.1 #V
	max_tens = 5 #V
	tens_step = args.tension_res

	# define the number of points for the voltage sweep:
	N_tens = int(len(np.arange(min_tens,max_tens,tens_step)))+1
	
	# connect to the Keithley power supply:
	'''
	rm = pyvisa.ResourceManager()
	addr = rm.list_resources() # USB0 is the top USB port in RPy, USB1 is the bottom one
	'''
	ps = myKeithley()
	ps.connect("ASRL/dev/ttyUSB1::INSTR")

	# connect to the PM5B power meter
	pm=PM5()
	pm.connect('USB0::1027::24577::856V::0::RAW')
	
	# PM5B settings:	
	pm.set_range(4,1) # 1->200uW, 2->2mW, 3->20mW, 4->200mW ; 1->range_hold=True
	time.sleep(5) # wait for the change of channel
	pm.set_zero()
	time.sleep(5) # wait for the stabilization
	
	# Keithley settings:
	ps.set_tensions(tension_CH1=8,tension_CH2=5,tension_CH3=4)
	ps.set_current_limitations(current_CH1=0.8,current_CH2=1.6,current_CH3=0.150)

	# switch on the output of the ps:
	ps.switch_on_output()
	time.sleep(1)
	
	# connect to Valon:
	myValon = Valon(port="/dev/ttyAMA4",baud=115200)
	myValon.set_freq(args.valon_freq/6 * 1000)
	print(f"Frequency of the Valon set to {args.valon_freq * 1000}MHz")
	
	time.sleep(45) # wait for pm stabilization
	
	print("measuring the power...")
	# acquire data
	count=0
	time_plot = []
	power = []

	time_in = time.time()
	while(count<100):
		power.append(pm.read_power())
		time_plot.append(time.time()-time_in)
		count+=1

	time_end = time.time()

	timeit = time_end-time_in
	print(f"single measure took {timeit} s")
	
	plt.plot(time_plot,power)
	plt.xlabel('time [s]')
	plt.ylabel('Power [W]')
	plt.show()

	time.sleep(3)

	# switch off the ps output
	ps.switch_off_output() 
	
	# close the connection with the Keithley power supply
	ps.close()

	# close the connection with the PM5B power meter
	pm.close()
