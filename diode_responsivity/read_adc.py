import sys
import time
import os

import yaml
import logging


sys.path.insert(0, "/home/polocalc/Documents/porter/porter/sensors")
sys.path.insert(0, "/home/polocalc/Documents/porter/porter")

import ads1015 as ads


def read_adc():
	
	cfg_filename = "/home/polocalc/Documents/porter/config/test_configs/adc_test_resp_config.yml"
	
	with open(cfg_filename, "r") as cfg:
		config = yaml.safe_load(cfg)
		logging.info(f"Loaded configuration {cfg_filename}")
        	
	adc_params = config["sensors"]["ADC_1"]
		
	adc = ads.ADS1015(adc_params["connection"]["parameters"]["channels"],
					  address=adc_params["connection"]["parameters"]["address"],
				      bus=adc_params["connection"]["parameters"]["bus"],
					  mode=adc_params["connection"]["parameters"]["mode"],
					  name=adc_params["name"],
					  )
					  
	adc.configure(adc_params["configuration"])
	
	print(adc.read())
	

if __name__ == "__main__":
	read_adc()
