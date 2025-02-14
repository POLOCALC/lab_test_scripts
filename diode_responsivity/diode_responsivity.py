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
	parser.add_argument("-l","--lower-tens",help="Lower limit on tension (V)",type=float,default=0.1)
	parser.add_argument("-u","--upper-tens",help="Upper limit on tension (V)",type=float,default=5)
	parser.add_argument("-f", "--valon-freq", help="Ouput frequency of the Valon (GHz)",type=float,default=93)
	parser.add_argument("-r", "--power-range",help="Power range of the power meter (mW)",type=float,default=200)
	args = parser.parse_args()
	
	# define max and min values for the tension applied to the multiplier attenuator and the step:
	min_tens = args.lower_tens
	max_tens = args.upper_tens
	tens_step = args.tension_res
	
	if(min_tens>max_tens):
		print("Invalid tension limits")
		exit()
	if(max_tens>5):
		print("Upper tension above 5V")
		exit()
	if(min_tens<0.1):
		print("Lower tension smaller than 0.1V")
		exit()

	# define the number of points for the voltage sweep:
	ps_tensions = np.arange(min_tens,max_tens+tens_step,tens_step)[::-1]
	
	# define the power meter range: 
	pm_ranges = [0.2,2,20,200] #mW

	if(args.power_range==200):
		pm_range_idx = 4
	elif(args.power_range==20):
		pm_range_idx = 3
	elif(args.power_range==2):
		pm_range_idx = 2
	elif(args.power_range==0.2):
		pm_range_idx = 1
	else:
		print("Invalid power meter range")
		exit()
		
	# connect to the PM5B power meter
	pm=PM5()
	pm.connect('USB0::1027::24577::856V::0::RAW')
	
	# PM5B settings:	
	pm.set_range(pm_range_idx,1) 
	time.sleep(10) # wait for the change of channel
	pm.set_zero()
	time.sleep(10) # wait for the stabilization
	
	# connect to the Keithley power supply: "ASRL/dev/ttyUSB0::INSTR"
	rm = pyvisa.ResourceManager()
	addr = rm.list_resources()
	ps = myKeithley()
	ps.connect(addr[0])
	
	# Keithley settings:
	ps.set_tensions(tension_CH1=8,tension_CH2=5,tension_CH3=args.upper_tens)
	ps.set_current_limitations(current_CH1=0.8,current_CH2=1.6,current_CH3=0.150)

	# switch on the output of the ps:
	ps.switch_on_output()
	time.sleep(5)
	
	# connect to Valon:
	myValon = Valon(port="/dev/ttyAMA4",baud=115200)
	time.sleep(3)
	myValon.get_freq()
	print(f"setting Valon freq to: {args.valon_freq/6 * 1000}")
	myValon.set_freq(args.valon_freq/6 * 1000)
	print(f"Frequency of the Valon set to {myValon.get_freq()}MHz")
	myValon.set_pwr(-6.5)
	
	time.sleep(30) # wait for pm stabilization
	
	for ch3_tens in ps_tensions:
		ps.set_single_tension(3,ch3_tens)
		time.sleep(10) # wait for stabilization
		
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
		
		pwr_thres = pm_ranges[pm_range_idx-2] - pm_ranges[pm_range_idx-2]*20/100
		print(np.mean(power))
		print(pwr_thres)
		
		if(np.mean(power)*1e3<pwr_thres):
			pm_range_idx = pm_range_idx-1
			pm.set_range(pm_range_idx,1) 
			time.sleep(30)
			
		time.sleep(3)

	# switch off the ps output
	ps.switch_off_output() 
	
	# close the connection with the Keithley power supply
	ps.close()

	# close the connection with the PM5B power meter
	pm.close()
