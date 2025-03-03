import argparse
import sys
import os
import time
import pyvisa
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import yaml
import logging

sys.path.insert(0, "/home/polocalc/Documents/lab_test_scripts/remote_Keithley") # add the path for the Keithley script
sys.path.insert(0, "/home/polocalc/Documents/lab_test_scripts/remote_PM5B") # add the path for the PM5B script
sys.path.insert(0, "/home/polocalc/Documents/porter/porter") # add the path for the valon
sys.path.insert(0, "/home/polocalc/Documents/porter/porter/sensors") # path for the adc

from pyKeithley import myKeithley
from pyPM5 import PM5
from valon import Valon
import ads1015 as ads

def read_pm_adc(init_time=time.time(),N_it=100,time_vec=[],pwr_vec=[],adc_vec=[]):
	"""
		Returns the power measured by power meter in mW, the tension of the diode in mV and the time needed to perform both the measurements
	"""
	count = 0
	while(count<N_it):
		pwr_vec.append(pm.read_power()*1e3)
		adc_vec.append(adc.read()*1e3)
		time_vec.append(time.time()-init_time)
		count+=1
	
	return time_vec,pwr_vec,adc_vec

if __name__ == "__main__":
	
	# initialization -------------------------------------------------------------------------------------------------------------------------
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-V", "--tension-res", help="Tension resolution (V)", type=float, default=0.1)
	parser.add_argument("-l","--lower-tens",help="Lower limit on tension (V)",type=float,default=0.1)
	parser.add_argument("-u","--upper-tens",help="Upper limit on tension (V)",type=float,default=5)
	parser.add_argument("-f","--valon-freq", help="Ouput frequency of the Valon (GHz)",type=float,default=93)
	parser.add_argument("-r","--power-range",help="Power range of the power meter (mW)",type=float,default=200)
	parser.add_argument("-p","--plot",help="Plot the measures",type=bool,default=False)
	parser.add_argument("-d", "--diode", help="diode used for measurements", type=str, default="hp")
	args = parser.parse_args()
	
	# create the folder to store data:
	now = datetime.now()
	dir_name = f"/home/polocalc/Documents/lab_test_scripts/diode_responsivity/{now.strftime('%Y_%m_%d_%H_%M_%S')}_{args.valon_freq}GHz"
	os.mkdir(dir_name)
	
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
		
	# check the diode name is correct:
	if((args.diode=="hp") or (args.diode=="vdi") or (args.diode=="eravant")):
		print(f"using {args.diode} diode")
	else:
		print("Invalid diode name")
		exit()
	
	# connection and configuration of instruments: -------------------------------------------------------------------------------------------------------
	
	# connect to the PM5B power meter
	pm=PM5()
	pm.connect('USB0::1027::24577::856V::0::RAW')
	
	# PM5B settings:	
	pm.set_range(4,1) # initially at 200mW for stabilization
	time.sleep(10) # wait for the change of channel
	pm.set_zero()
	time.sleep(10) # wait for the stabilization
	
	# connect to the Keithley power supply: "ASRL/dev/ttyUSB0::INSTR"
	rm = pyvisa.ResourceManager()
	addr = rm.list_resources()
	ps = myKeithley()
	ps.connect(addr[0])
	
	# Keithley settings:
	ps.set_tensions(tension_CH1=9,tension_CH2=5,tension_CH3=5) # initially no attenuation
	ps.set_current_limitations(current_CH1=0.8,current_CH2=1.6,current_CH3=0.150)

	# switch on the output of the ps:
	ps.switch_on_output()
	time.sleep(5)
	
	# connect to Valon:
	myValon = Valon(port="/dev/ttyAMA4",baud=115200)
	myValon.get_freq()
	print(f"setting Valon freq to: {args.valon_freq/6 * 1000}")
	myValon.set_freq(args.valon_freq/6 * 1000)
	print(f"Frequency of the Valon set to {myValon.get_freq()}MHz")
	myValon.set_pwr(-6.5)
	myValon.stop_amd()
	print(f"Valon modulation: {myValon.get_amd()}")
	
	# configure the adc:
	if(args.diode=="hp"):
		config_gain = 16
		config_dr = 1600
	elif(args.diode=="vdi"):
		config_gain = 16
		config_dr = 1600
	elif(args.diode=="eravant"):
		config_gain = 16
		config_dr = 1600
	
	adc_params = {'gain': config_gain, 'data_rate': config_dr}
        			
	adc = ads.ADS1015(channel=[0,1],
					  address=0x48,
				      bus=6,
					  mode="differential",
					  name="ADS1015",
					  )
					  
	adc.configure(adc_params)
	
	# create the log file -------------------------------------------------------------------------------------------------------------------------
	
	log_file_name = f"{dir_name}/log_file.txt"
	log_file = open(log_file_name,"w")
	log_file.write(f"Multiplier output frequency (GHz): {args.valon_freq}\n\n")
	log_file.write(f"Valon output frequency (MHz): {myValon.get_freq()}\n\n")
	log_file.write(f"Valon output power (dBm): {myValon.get_pwr()}\n\n")
	log_file.write(f"Valon modulation: OFF \n\n")
	log_file.write(f"Keithley channels: {ps.return_settings()}\n\n")
	log_file.write(f"Upper sweep tension (V): {max_tens}\n")
	log_file.write(f"Lower sweep tension (V): {min_tens}\n")
	log_file.write(f"Sweep tension step (V): {tens_step}\n")
	log_file.close()
	
	# wait for the stabilization of the power: ----------------------------------------------------------------------------------------------------
	
	print(f"wait for stabiization...")
	
	# create the file
	stabil_file_name = f"{dir_name}/pwr_stabilization.txt"
	stabil_file = open(stabil_file_name,"a")
	stabil_file.write(f"time(s)				pwr(mW)				adc(mV)	\n")
	
	#read the first 100 data:
	
	init_time = time.time()
	time_arr,pwr_arr,adc_arr = read_pm_adc(init_time=init_time)
	
	pwr_comparison = [p for p in pwr_arr if p!=-np.inf]
	
	avg_stab = np.mean(pwr_comparison)
	std_stab = np.std(pwr_comparison)
	
	print(f"avg pwr: {avg_stab}")
	print(f"std pwr: {std_stab}")
	frac_avg_goal = 1/2000*avg_stab
	print(f"goal: {frac_avg_goal}")
	
	# cycle to check if the pwr is stabilized:
	i=1 
	while(std_stab>frac_avg_goal):
		
		time_arr,pwr_arr,adc_arr = read_pm_adc(init_time=init_time,time_vec=time_arr,pwr_vec=pwr_arr,adc_vec=adc_arr)
		
		pwr_comparison = pwr_arr[-100:]
		pwr_comparison = [p for p in pwr_comparison if p!=-np.inf]
		
		avg_stab = np.mean(pwr_comparison)
		std_stab = np.std(pwr_comparison)
		frac_avg_goal = 1/2000*avg_stab
		
		if(time_arr[-1]>60*(5*i)):
			print(f"time past: {time_arr[-1]}s")
			print(f"avg pwr: {avg_stab}")
			print(f"std pwr: {std_stab}")
			print(f"goal: {frac_avg_goal}")
			i+=1
	
	for t,p,V in zip(time_arr,pwr_arr,adc_arr):
		stabil_file.write(f"{t}		{p}		{V} \n")
	
	stabil_file.close()
	
	# voltage sweep ---------------------------------------------------------------------------------------------------------------------------------------
	
	voltage_sweep_dir = f"{dir_name}/Voltage_sweep"
	os.mkdir(voltage_sweep_dir)
	
	# set the pm range:
	pm.set_range(pm_range_idx,1)
	
	neg_pwr_meas = False
		
	# start the voltage sweep 
	for ch3_tens in ps_tensions:
		
		tens_file_name = f"{voltage_sweep_dir}/{'{:.2f}'.format(ch3_tens)}V.txt"
		tens_file = open(tens_file_name,"w")
		tens_file.write(f"Attenuator tension (V): {'{:.2f}'.format(ch3_tens)}\n")
		tens_file.write(f"PM5 range: {pm_ranges[pm_range_idx-1]} mW \n\n")
		tens_file.write(f"time(s)				pwr(mW)	\n")
		
		ps.set_single_tension(3,float('{:.2f}'.format(ch3_tens)))
		time.sleep(10) # wait for stabilization
		
		print("measuring the power...")
		
		# acquire data
		
		time_plot,power,adc_tension = read_pm_adc(init_time=time.time(),N_it=100,time_vec=[],pwr_vec=[],adc_vec=[])
		
		# change the pm range if needed, skip if the range is already 200uW
		if not (pm_ranges[pm_range_idx-1]==0.2):
		
			pwr_thres = pm_ranges[pm_range_idx-2] - pm_ranges[pm_range_idx-2]*10/100
			print(f"avg pwr: {np.mean(power[power!=np.inf])}")
			print(f"pwr_thresh: {pwr_thres}")
		
			if(np.mean(power[power!=np.inf])<pwr_thres):
				pm_range_idx = pm_range_idx-1
				pm.set_range(pm_range_idx,1) 
				time.sleep(30)
		
		# if the pwr is negative:
		if(np.any(power[power!=-np.inf]<0)):
			
			print("Measured a negative power: starting the dedicated procedure")
			
			time_init_neg = time.time()
			
			# 1st iteration
			ps.switch_off_output()  
			time.sleep(45)	# wait for stabilization 
			time_neg,pwr_neg,adc_neg = read_pm_adc(init_time=time_init_neg,N_it=50,time_vec=[],pwr_vec=[],adc_vec=[]) # read the zero (no pwr) level
			
			ps.switch_on_output() 
			time.sleep(5)
	
			# connect to Valon:
			myValon = Valon(port="/dev/ttyAMA4",baud=115200)
			myValon.set_freq(args.valon_freq/6 * 1000)
			myValon.set_pwr(-6.5)
			print(f"Valon set to {myValon.get_freq()}, {myValon.get_pwr()} ")
			myValon.stop_amd()
			
			time.sleep(45)	# wait for stabilization 
			time_neg,pwr_neg,adc_neg = read_pm_adc(init_time=time_init_neg,N_it=50,time_vec=time_neg,pwr_vec=pwr_neg,adc_vec=adc_neg) # read the pwr on level
			
			it=1
			while(it<5): # iterate 5 times
				
				ps.switch_off_output()  
				time.sleep(45)	# wait for stabilization 
				time_neg,pwr_neg,adc_neg = read_pm_adc(init_time=time_init_neg,N_it=50,time_vec=time_neg,pwr_vec=pwr_neg,adc_vec=adc_neg) # read the zero (no pwr) level
			
				ps.switch_on_output() 
				time.sleep(5)
				
				# connect to Valon:
				myValon = Valon(port="/dev/ttyAMA4",baud=115200)
				myValon.set_freq(args.valon_freq/6 * 1000)
				myValon.set_pwr(-6.5)
				print(f"Valon set to {myValon.get_freq()}, {myValon.get_pwr()} ")
				myValon.stop_amd()
				
				time.sleep(45)	# wait for stabilization 
				time_neg,pwr_neg,adc_neg = read_pm_adc(init_time=time_init_neg,N_it=50,time_vec=time_neg,pwr_vec=pwr_neg,adc_vec=adc_neg) # read the pwr on level
				
				it+=1
			
			
			for t,p,V in zip(time_neg,pwr_neg,adc_neg):
				tens_file.write(f"{t}		{p}		{V}	\n")
			
		else:
			for t,p,V in zip(time_plot,power,adc_tension):
				tens_file.write(f"{t}		{p}		{V}	\n")
				
				
		if args.plot:
			fig,ax = plt.subplots(nrows=1,ncols=2,figsize=(16,7))
		
			ax[0].plot(time_plot,power)
			ax[0].set_xlabel('time [s]')
			ax[0].set_ylabel('Power [mW]')
		
			ax[1].plot(time_plot,adc_tension)
			ax[1].set_xlabel('time [s]')
			ax[1].set_ylabel('ADC tension [mV]')
		
			plt.show()
			

	tens_file.close()
	
	# disconnection ----------------------------------------------------------------------------------------------------------------------------------
	
	# switch off the ps output
	ps.switch_off_output() 
	
	# close the adc
	adc.close()
	
	# close the connection with the Keithley power supply
	ps.close()

	# close the connection with the PM5B power meter
	pm.close()
