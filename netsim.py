import os
import sys
import argparse
import docker
import pyroute2
import yaml
from modules import Network
from termcolor import colored, cprint

current_directory = os.getcwd()
# Docker client and API
client = docker.from_env()
client_api = docker.APIClient()

# Netlink
ipr = pyroute2.IPRoute()

# Argument Parser
parser = argparse.ArgumentParser()
parser.add_argument("cmd", help="command to run : start, stop")
parser.add_argument("path", help="network file location")
args = parser.parse_args()

os.system('echo 0 > /proc/sys/net/bridge/bridge-nf-call-iptables')

# Start the network
if args.cmd == 'start':
	network = Network(args.path)
	network.start_bridges(ipr)
	network.start_hosts(client, client_api)
	network.create_links(ipr, client)

# Stop the network
elif args.cmd == 'stop':
	network = Network(args.path)
	network.stop_bridges(ipr)
	network.stop_hosts(client)
	#network.remove_links(ipr)
	
	



