import os
import sys
import argparse
import docker
import yaml
from termcolor import colored, cprint

current_directory = os.getcwd()
client = docker.from_env()

hosts = []
host_names = []


parser = argparse.ArgumentParser()
parser.add_argument("cmd", help="command to run : init, stop")
parser.add_argument("path", help="network file location")
args = parser.parse_args()

# Parse the network's yaml file and get hosts / host names
def parse_yaml(path):
	with open(path, 'r') as stream:
		topology = yaml.load(stream)
		
		global hosts
		global host_names
		hosts = topology['hosts']
		host_names = [ h['name'] for h in hosts ]


# Run the network (run containers)
def init_network():
	for host in hosts:
		container_image = host['image']
		container_name = host['name']

		if 'volume' in host: 
			volume = host['volume']
			local_volume_path = volume[0]
			container_volume_path = volume[1]
			client.containers.run(container_image, name=container_name, volumes={local_volume_path : {'bind': container_volume_path, 'mode':'rw'}}, detach=True)

		else :
			client.containers.run(container_image, name=container_name, detach=True)

		cprint(container_name + ' started', 'green', end='\n')

# Stop the network (stop and remove containers)
def stop_network():
	for container_name in host_names:
		client.containers.get(container_name).stop(timeout=0)
		client.containers.get(container_name).remove()
		cprint(container_name + ' stopped', 'green', end='\n')


parse_yaml(args.path)


if args.cmd == 'init':
	init_network()

elif args.cmd == 'stop':
	stop_network()
	



