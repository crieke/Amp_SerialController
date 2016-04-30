#!/usr/bin/env python
import time
import serial
import sys
import urllib

# Set Variables here
squeezepi_input = 'coax2'
sonos_input = 'opt1'
amp_poweroff_cmd = 'power_off'
sonosip = '10.0.1.34'
rs232port = '/dev/ttyUSB0'
rs232baudrate = 115200
logging = False



## Initializing some needed Variables
playing = [amp_poweroff_cmd]
lastplaying = []
running = True

## Initializing RS232 Connection to Amp...
ser = serial.Serial(
	port=rs232port,
	baudrate=rs232baudrate,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS
	)

## Loop to check devices status...
while running ==  True:
	if logging: print '#############################################'

	input = '' #reset last string
	playerswitch = '' #reset last string
	
	## Check if squeezepi is currently turned on (via active display backlight)...
	squeezepi = not bool(int(open('/sys/class/backlight/rpi_backlight/bl_power', 'r').read()))
	if squeezepi and 'squeezepi' not in playing: playing.append('squeezepi')
	if not squeezepi and 'squeezepi' in playing: playing.remove('squeezepi')
	
	## Check if Sonos is currently playing...
	try:
		sonosamp = urllib.urlopen('http://' + sonosip + ':1400/status/perf').read()
	except:
		sonosamp = "Not available"

	for sonosampstate in sonosamp.split("\n"):
		if "currently" in sonosampstate:
			sonosamp = sonosampstate.strip()
	if 'PLAYING' in sonosamp:
		if 'sonos' not in playing:	playing.append('sonos')
	else:
		if 'sonos' in playing: playing.remove('sonos')

	## Getting amp information through RS232
	ser.isOpen()
	ser.write('get_display!')
	ampstatus = ''
	time.sleep(1)
	while ser.inWaiting() > 0:
		ampstatus += ser.read(1)
	#if logging: print ampstatus
	
	
	## Based on the "VOL" in the display, you know the device is powered on...
	if 'VOL' in ampstatus:
		amppower = True
		if squeezepi_input.upper() in ampstatus: current_input = squeezepi_input
		elif sonos_input.upper() in ampstatus: current_input = sonos_input
	else: 
		current_input = ''
		amppower = False


	## Echo current settings for logging purposes.
	if logging:
		print 'Amp-Power: ' + str(amppower)
		print 'squeezepi: ' + str(squeezepi)
		print 'sonos: ' + str('sonos' in playing)
		if playerswitch: print 'switch: ' + str(playerswitch != '')
		if len(playing) > 1: print 'Selected Player: ' + str(playing[-1])
		if current_input != '': print 'Current input: ' + str(current_input)
		if len(playing) > 1: print 'Active Players: ' + str(playing[1:3])

	if lastplaying != playing:
		playerswitch = True 
		lastplaying = playing[:]

			
		# This if-condition is called if the state of one device has been changed or if the gained info from the devices mismatch. 
	if playerswitch:
		if len(playing) > 1:
				if current_input != eval(str(playing[-1]) + '_input'): 
					input = eval(str(playing[-1]) + '_input')
					print 'Changing to input: ' + eval(str(playing[-1]) + '_input')
		else: 
			if amppower:
				input = amp_poweroff_cmd
		
		
		if input != '':
			ser.write(input + '!')
			if logging: print '*** Sending RS232 Command! ***  (' + input + ')'
	# Python 3 users
	# input = input(">> ")
	# send the character to the device
	# (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
			out = ''
	# let's wait one second before reading output (let's give device time to answer)
			time.sleep(2)
			while ser.inWaiting() > 0:
				out += ser.read(1)
	
			#if out != '':
				#if logging: print "amp: " + out
ser.close()
exit()
