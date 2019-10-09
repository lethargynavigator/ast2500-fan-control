# ast2500-fan-control
Python script to control fan speed on ASPEED AST2500 BMC

Uses ipmitool to detect CPU temp and control fan speeds

Uses hddtemp to detect hdd temps

I'm using this on an Asrock X470D4U, but it might work with other motherboards with an ASPEED BMC.

Notes:<br>
fancontrol_cpu_only.py does what the name says.<br>
The fan speed detection functions are currently unused. I'll use them for validation of fan speed changes if I find it necessary.<br>
As a safety, the hdd temp and cpu temp detection functions are designed to set the fans to full speed if an exception is caught.<br>

Requirements:<br>
python 3<br>
ipmitool<br>
hddtemp<br>
needs to run as root for ipmitool to work<br>

TODO:<br>
set fans to full speed on exit<br>
write systemd service<br>
