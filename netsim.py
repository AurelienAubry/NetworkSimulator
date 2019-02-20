import os
import sys
import argparse
import docker
import pyroute2
import yaml
from termcolor import colored, cprint

current_directory = os.getcwd()
client = docker.from_env()

hosts = []
host_names = []
bridges = []
links = []


parser = argparse.ArgumentParser()
parser.add_argument("cmd", help="command to run : start, stop")
parser.add_argument("path", help="network file location")
args = parser.parse_args()
ipr = pyroute2.IPRoute()

# Parse the network's yaml file and get hosts / host names
def parse_yaml(path):
	with open(path, 'r') as stream:
		network = yaml.load(stream)
		
		global hosts
		global host_names
		global bridges
		global links

		topology = network['network']
		hosts = topology['hosts']
		host_names = [ h['name'] for h in hosts ]
		bridges = topology['bridges']
		links = topology['links']


# Run the network (run containers)
def start_network():
	start_bridges()
	start_hosts()

def start_bridges():
	cprint('======[ BRIDGES ]======', 'blue', end='\n')
	for bridge in bridges:
		bridge_name = bridge['name']
		bridge_address = bridge['address']

		bridge_address_mask = bridge_address.split('/')

		ipr.link("add", ifname=bridge_name, kind="bridge")
		dev = ipr.link_lookup(ifname=bridge_name)[0]

		ipr.link("set", index=dev, state="up")
		ipr.addr("add", index=dev, address=bridge_address_mask[0],mask=int(bridge_address_mask[1]))

		cprint(bridge_name + ' added', 'green', end='\n')

def start_hosts():
	cprint('======[ HOSTS ]======', 'blue', end='\n')
	for host in hosts:
		container_image = host['image']
		container_name = host['name']
		# Container with volume
		if 'volume' in host: 
			volume = host['volume']
			local_volume_path = volume[0]
			container_volume_path = volume[1]
			client.containers.run(container_image, name=container_name, volumes={local_volume_path : {'bind': container_volume_path, 'mode':'rw'}}, detach=True)
		
		# Container without volume
		else :
			client.containers.run(container_image, name=container_name, detach=True)
		
		cprint(container_name + ' started', 'green', end='\n')

# Stop the network (stop and remove containers)
def stop_network():
	stop_hosts()
	stop_bridges()
	
def stop_hosts():
	cprint('======[ HOSTS ]======', 'blue', end='\n')
	for container_name in host_names:
		client.containers.get(container_name).stop(timeout=0)
		client.containers.get(container_name).remove()
		cprint(container_name + ' stopped', 'green', end='\n')

def stop_bridges():
	cprint('======[ BRIDGES ]======', 'blue', end='\n')
	for bridge in bridges:
		bridge_name = bridge['name']
		dev = ipr.link_lookup(ifname=bridge_name)[0]
		ipr.link("delete", index=dev, kind="bridge")
		cprint(bridge_name + ' removed', 'green', end='\n')
		


parse_yaml(args.path)


if args.cmd == 'start':
	start_network()

elif args.cmd == 'stop':
	stop_network()
	



