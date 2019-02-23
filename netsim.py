import os
import sys
import argparse
import docker
import pyroute2
import yaml
from modules import Network
from termcolor import colored, cprint

current_directory = os.getcwd()
client = docker.from_env()
client_api = docker.APIClient()

parser = argparse.ArgumentParser()
parser.add_argument("cmd", help="command to run : start, stop")
parser.add_argument("path", help="network file location")
args = parser.parse_args()
ipr = pyroute2.IPRoute()

if args.cmd == 'start':
	network = Network(args.path)
	network.start_bridges(ipr)
	network.start_hosts(client, client_api)
	network.create_links(ipr, client)

elif args.cmd == 'stop':
	network = Network(args.path)
	network.stop_bridges(ipr)
	network.stop_hosts(client)
	#network.remove_links(ipr)
	
	



