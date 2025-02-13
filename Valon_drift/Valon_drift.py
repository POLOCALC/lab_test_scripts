import sys
import argparse
import time
from datetime import datetime

sys.path.insert(0,"/home/polocalc/Documents/porter/porter")
from valon import Valon

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--valon-freq",help="Ouput frequency of the Valon (GHz)",type=float,default=93)
	parser.add_argument("-p", "--valon-pwr",help="Valon output power (dBm)",type=float,default=2)
	parser.add_argument("-d","--time-duration",help="Time duration of the data acquisition (s)",type=int,default=10)
	parser.add_argument("-s","--time-step",help="Time step between two measures (s)",type=float,default=2)
	args = parser.parse_args()
	
	myVal = Valon(port="/dev/ttyAMA4",baud=115200)
	myVal.set_freq(args.valon_freq * 1000) 
	myVal.set_pwr(args.valon_pwr)
	
	temp = []
	pwr = []
	time_vec = []
	
	init_time = time.time()
	
	while((time.time()-init_time)<args.time_duration):
		time_vec.append(time.time()-init_time)
		temp.append(myVal.get_temp())
		#pwr.append(myVal.get_pwr())
		time.sleep(args.time_step)
	
	now = datetime.now()
	file_name = f"{now.strftime('%Y_%m_%d_%H_%M_%S')}_{args.valon_freq}GHz"
	
	f = open(file_name,"w")
	f.write(f"{now.strftime('%Y/%m/%d %H:%M:%S')} \n")
	f.write(f"Time duration: {args.time_duration}s, time step: {args.time_step}s \n")
	f.write(f"Frequency: {args.valon_freq}GHz \n")
	f.write(f"Output power: {args.valon_pwr}dBm \n\n")
	f.write(f"time(s)				temp(degC)	\n")
	
	for t,tv in zip(temp,time_vec):
		f.write(f"{tv}		{t}	\n")
		
	f.close()
	
	myVal.close_connection()
	
