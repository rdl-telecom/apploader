import netifaces as ni
import re

ip_prefix = re.compile(r'^10\.10\.\d{1,3}\.\d{1,3}')

def ip2int(ip):
	result = 0
	i = 3
	for octet in ip.split('.'):
		result += int(octet) << 8 * i
		i -= 1
	return result

def int2ip(num):
	octets = []
	for i in [ 3 - n for n in range(4) ]:
		octets.append(str((num >> 8 * i) & 255))
	return '.'.join(octets)

class Networking:
	source = None
	destination = None
	ip_list = []
	def __init__(self):
		for iface in ni.interfaces():
			addresses = ni.ifaddresses(iface)
			if ni.AF_INET in addresses:
				ip4_info = addresses[ni.AF_INET]
				for info in ip4_info:
					self.ip_list.append(info['addr'])
					if ip_prefix.match(info['addr']):
						self.source = info['addr']
						self.destination = int2ip((ip2int(info['addr']) & ip2int(info['netmask'])) + 1)