#!/usr/bin/python3

import subprocess
import re
import time
import datetime

# path to ipmitool
ipmitool = '/usr/bin/ipmitool'

# path to log file
logfile = '/root/scripts/fan_control.log'

# temperatures for cpu cooling override
# script polls cpu temp once a second
# if cpu temp goes above cpu_override_temp, all fans will be set to 100%
# if cpu temp goes below cpu_normal_temp, all fans will return to normal speed (fan_default var)
cpu_override_temp = 65
cpu_normal_temp = 55

# normal cpu fan speed, as a % of max
# this value is set when the script starts and when not in cpu temperature override mode
# 0 = "smart fan" mode
fan_default = 0

# various globals
fanspeed = hex(fan_default)
cpuoverride = False
allfansnormal = [ipmitool,'raw','0x3a','0x01',fanspeed,fanspeed,fanspeed,fanspeed,fanspeed,fanspeed,fanspeed,fanspeed]
allfanshigh = [ipmitool,'raw','0x3a','0x01','0x64','0x64','0x64','0x64','0x64','0x64','0x64','0x64']

cpufanspeed = re.compile(r'^FAN1.*\|\s([0-9][0-9][0-9]|[0-9][0-9][0-9][0-9])\sRPM$', re.MULTILINE)
cputemp = re.compile(r'^CPU\sTemp.*\|\s([0-9][0-9])\sdegrees\sC$', re.MULTILINE)

def log(message):
    with open(logfile,'a') as log:
        log.write(str(datetime.datetime.now()))
        log.write(' ')
        log.write(str(message))
        log.write('\n')

def getcpufanspeed():
    try:
        time.sleep(3)
        speed = subprocess.check_output([ipmitool,'sdr','type','Fan']).decode('utf-8')
        speed = re.search(cpufanspeed, speed)
        speed = speed.group(1)
        return int(speed)
    except Exception as e:
        log(e)

def getcputemp():
    try:
        temp = subprocess.check_output([ipmitool,'sdr','type','Temperature']).decode('utf-8')
        temp = re.search(cputemp, temp)
        temp = temp.group(1)
        return int(temp)
    except Exception as e:
        log(e)
        subprocess.run(allfanshigh)
        log('cpu temp detection failure, all fans set to 100%')

def checkcputemp():
    global currentcpufanspeed
    global cpuoverride
    try:
        currentcputemp = getcputemp()
        if currentcputemp > cpu_override_temp and cpuoverride == False:
            subprocess.run(allfanshigh)
            cpuoverride = True
            log('cpu temp > '+str(cpu_override_temp)+'C, all fans set to 100%')
        elif currentcputemp < cpu_normal_temp and cpuoverride == True:
            subprocess.run(allfansnormal)
            cpuoverride = False
            log('cpu temp < '+str(cpu_normal_temp)+'C, cpu fan set to '+str(fan_default)+'%')
    except Exception as e:
        log(e)

while True:
    checkcputemp()
    time.sleep(1)
