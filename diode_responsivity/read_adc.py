import sys
import time
import os

import yaml
import logging
import argparse


sys.path.insert(0, "/home/polocalc/Documents/porter/porter/sensors")
sys.path.insert(0, "/home/polocalc/Documents/porter/porter")

import ads1015 as ads


def read_adc(config_gain="16",config_dr=1600):
	
	cfg_filename = "/home/polocalc/Documents/porter/config/test_configs/adc_test_resp_config.yml"
	
	with open(cfg_filename, "r") as cfg:
		config = yaml.safe_load(cfg)
		logging.info(f"Loaded configuration {cfg_filename}")
		
	cfg.close()
        	
	adc_params = {'gain': config_gain, 'data_rate': config_dr}
			
	adc = ads.ADS1015(channel=[0,1],
					  address=0x48,
				      bus=6,
					  mode="differential",
					  name="ADS1015",
					  )
					  
	adc.configure(adc_params)
	
	print(adc.read())
	

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-g", "--gain-config", help="gain configuration", type=str, default="16")
	parser.add_argument("-d", "--data-rate-config", help="data rate configuration", type=int, default=1600)
	args = parser.parse_args()
	
	read_adc(args.gain_config,args.data_rate_config)
