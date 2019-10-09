#!/root/venv/fan_control/bin/python3

import subprocess
import re
import time
import datetime

# path to ipmitool
ipmitool = '/usr/bin/ipmitool'

# path to hddtemp
hddtemp = '/usr/sbin/hddtemp'

# list of disks to poll for temperature
hdds = ['/dev/sda','/dev/sdb','/dev/sdc','/dev/sdd','/dev/sde','/dev/sdf','/dev/sdg','/dev/sdh']

# path to log file
logfile = '/root/venv/fan_control/logs'

# temperatures for cpu cooling override
# script polls cpu temp once a second
# if cpu temp goes above cpu_override_temp, all fans will be set to 100%
# if cpu temp goes below cpu_normal_temp, cpu fan will return to 50%, hd fans will return to previous speed
cpu_override_temp = 69
cpu_normal_temp = 60

# normal cpu fan speed, as a % of max
# this value is set when the script starts and when not in cpu temperature override mode
cpu_fan_default = 50

# hd temperature polling interval in seconds
hd_poll = 180

# hd fan speeds, expressed as % of max
hd_fans_default = 50
hd_fans_hi = 100
hd_fans_medhi = 75
hd_fans_medlo = 50
hd_fans_lo = 25

# hd target temperatures
# if any hd temp >= hd_hi, hd_fans_hi will be set
hd_hi = 41
# if any hd temp == hd_medhi, hd_fans_medhi will be set
hd_medhi = 40
# if any hd temp == hd_medhi, hd_fans_medlo will be set
hd_medlo = 39
# if all hd temps <= hd_lo, hd_fans_lo will be set
hd_lo = 38

# various globals
hdchecktime = time.time()
currentcpufanspeed = hex(cpu_fan_default)
currenthdfanspeed = hex(hd_fans_default)
cpuoverride = False
hdfanspeed = [ipmitool,'raw','0x3a','0x01',currentcpufanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed]
allfanshigh = [ipmitool,'raw','0x3a','0x01','0x64','0x64','0x64','0x64','0x64','0x64','0x64','0x64']
cputemp = re.compile(r'^CPU\sTemp.*\|\s([0-9][0-9])\sdegrees\sC$', re.MULTILINE)
cpufanspeed = re.compile(r'^FAN1.*\|\s([0-9][0-9][0-9]|[0-9][0-9][0-9][0-9])\sRPM$', re.MULTILINE)
matchhdfanspeed = re.compile(r'^FAN3.*\|\s([0-9][0-9][0-9]|[0-9][0-9][0-9][0-9])\sRPM$', re.MULTILINE)
exhaustfanspeed = re.compile(r'^FAN5.*\|\s([0-9][0-9][0-9]|[0-9][0-9][0-9][0-9])\sRPM$', re.MULTILINE)
cpufan_max_speed = 3000
hdfan_max_speed = 2800
exhaustfan_max_speed = 2200

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
            subprocess.run(hdfanspeed)
            cpuoverride = False
            log('cpu temp < '+str(cpu_normal_temp)+'C, cpu fan set to '+str(cpu_fan_default)+'%')
    except Exception as e:
        log(e)

def gethdfanspeed():
    try:
        time.sleep(3)
        speed = subprocess.check_output([ipmitool,'sdr','type','Fan']).decode('utf-8')
        speed = re.search(matchhdfanspeed, speed)
        speed = speed.group(1)
        return int(speed)
    except Exception as e:
        log(e)

def getexhaustfanspeed():
    try:
        time.sleep(3)
        speed = subprocess.check_output([ipmitool,'sdr','type','Fan']).decode('utf-8')
        speed = re.search(exhaustfanspeed, speed)
        speed = speed.group(1)
        return int(speed)
    except Exception as e:
        log(e)

def hdtemp(dev):
    try:
        temp = subprocess.check_output([hddtemp,dev])
        temp = re.match('^.*([0-9][0-9])°C$', temp.decode('utf-8'))
        temp = temp.group(1)
        return temp
    except Exception as e:
        log(e)
        subprocess.run(allfanshigh)
        log('hd temp detection failure, all fans set to 100%')

def checkhdtemps():
    hdtemps = []
    global hdchecktime
    global currenthdfanspeed
    global hdfanspeed
    if cpuoverride == False:
        try:
            for hdd in hdds:
                hdtemps.append(int(hdtemp(hdd)))
            if any(x >= hd_hi for x in hdtemps):
                currenthdfanspeed = hex(hd_fans_hi)
                hdfanspeed = [ipmitool,'raw','0x3a','0x01',currentcpufanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed]
                subprocess.run(hdfanspeed)
                log('hd temp >= '+str(hd_hi)+',C fans set to '+str(hd_fans_hi)+'%')
            elif any(x == hd_medhi for x in hdtemps):
                currenthdfanspeed = hex(hd_fans_medhi)
                hdfanspeed = [ipmitool,'raw','0x3a','0x01',currentcpufanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed]
                subprocess.run(hdfanspeed)
                log('hd temp '+str(hd_medhi)+',C fans set to '+str(hd_fans_medhi)+'%')
            elif any(x == hd_medlo for x in hdtemps):
                currenthdfanspeed = hex(hd_fans_medlo)
                hdfanspeed = [ipmitool,'raw','0x3a','0x01',currentcpufanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed]
                subprocess.run(hdfanspeed)
                log('hd temp '+str(hd_medlo)+'C, fans set to '+str(hd_fans_medlo)+'%')
            elif all(x <= hd_lo for x in hdtemps):
                currenthdfanspeed = hex(hd_fans_lo)
                hdfanspeed = [ipmitool,'raw','0x3a','0x01',currentcpufanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed,currenthdfanspeed]
                subprocess.run(hdfanspeed)
                log('hd temp <= '+str(hd_lo)+'C, fans set to '+str(hd_fans_lo)+'%')
        except Exception as e:
            log(e)
    else:
        log('cpu temp override active, no action taken on hd fans')
    hdchecktime = time.time()

checkhdtemps()

while True:
    checkcputemp()
    currenttime = time.time()
    if currenttime - hdchecktime >= hd_poll:
        checkhdtemps()
    time.sleep(1)
