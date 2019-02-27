import os
import sys
import argparse
import pyroute2
import yaml
import subprocess
from termcolor import colored, cprint

# ================= #
#      Network	    #
# ================= #
class Network:

	# Init : parse the given yaml file 
	def __init__(self, path):

		with open(path, 'r') as stream:
			network = yaml.load(stream)
			topology = network['network']
			
			# Parse the HOSTS
			self.hosts = []
			for host in topology['hosts'] :
				if 'volume' in host:
					self.hosts.append(Node(host['name'], host['image'], host['volume']))
				else:
					self.hosts.append(Node(host['name'], host['image'], None))

			# Parse the LINKS and INTERFACES
			self.links = []
			self.interfaces = []
			for link in topology['links']:
				# Split the link
				interfaces = link.split('-')

				# Interfaces infos (host, name, adresse)
				interface1_info = interfaces[0].split(':')
				interface2_info = interfaces[1].split(':')
				
				# Find linked hosts
				host1 = Node(None, None, None)
				host2 = Node(None, None, None)
			
				for host in self.hosts :
					if host.get_name() == interface1_info[0]:
						host1 = host
					elif host.get_name() == interface2_info[0]:
						host2 = host
				
				# Interfaces with the given name / host / adress 
				interface1 = NodeInterface(host1.get_name() + str(interface1_info[1]), host1, interface1_info[2], host1.get_name() )
				interface2 = NodeInterface(host2.get_name() + str(interface2_info[1]), host2, interface2_info[2], host2.get_name() )

				# Register interfaces
				self.interfaces.append(interface1)
				self.interfaces.append(interface2)

				# Register link
				self.links.append(Link(interface1, interface2))

			# Parse the BRIDGES			
			self.bridges = []
			for bridge in topology['bridges']:

				current_bridge = Bridge(bridge['name'], bridge['address'])
				
				self.bridges.append(current_bridge)

				for link in bridge['links']:
					
					host_interface_info = link.split(':')
					host = Node(None, None, None)

					for h in self.hosts :
						if h.get_name() == host_interface_info[0]:
							host = h

					host_interface = NodeInterface(host.get_name() + str(host_interface_info[1]), host, host_interface_info[2], host.get_name())
					bridge_interface = BridgeInterface(current_bridge.get_name() + host.get_name() + str(host_interface_info[1]), current_bridge, bridge['address'], current_bridge.get_name())
					
					# Register interfaces
					self.interfaces.append(host_interface)
					self.interfaces.append(bridge_interface)
					
					# Register link
					self.links.append(Link(host_interface, bridge_interface))
				
				
	
	# Start the HOSTS
	def start_hosts(self, client, client_api):
		cprint('======[ HOSTS ]======', 'blue', end='\n')
		for host in self.hosts:
			host.start(client, client_api)
			#host.open_shell(client)
	
	# Stop the HOSTS
	def stop_hosts(self, client):
		cprint('======[ HOSTS ]======', 'blue', end='\n')
		for host in self.hosts:
			host.stop(client)

	# Start the BRIDGES
	def start_bridges(self, ipr):
		cprint('======[ BRIDGES ]======', 'blue', end='\n')
		for bridge in self.bridges:
			bridge.start(ipr)
	
	# Stop the BRIDGES
	def stop_bridges(self, ipr):
		cprint('======[ BRIDGES ]======', 'blue', end='\n')
		for bridge in self.bridges:
			bridge.stop(ipr)

	# Create the LINKS
	def create_links(self, ipr, client):
		cprint('======[ LINKS ]======', 'blue', end='\n')
		for link in self.links:
			link.create(ipr, client)

	# def remove_links(self, ipr):
	#	cprint('======[ LINKS ]======', 'blue', end='\n')
	#	for link in self.links:
	#		link.remove(ipr)



# ====================== #
#      Linux Bridge	 #
# ====================== #

class Bridge:

	# Init
	def __init__(self, name, address):
		self.name = name
		self.address = address
		self.interfaces = []

	# Create and start the bridge
	def start(self, ipr):
		
		bridge_address_mask = self.address.split('/')

		# Add the bridge (ip link add bridge_name type bridge)
		ipr.link("add", ifname=self.name, kind="bridge")
		
		# The created bridge
		dev = ipr.link_lookup(ifname=self.name)[0]

		# Set the bridge "up"
		ipr.link("set", index=dev, state="up")
		
		# Set the bridge IP address
		ipr.addr("add", index=dev, address=bridge_address_mask[0],mask=int(bridge_address_mask[1]))

		cprint(self.name + ' added', 'green', end='\n')
	
	# Getters
	def get_name(self):
		return self.name

	# Remove the bridge
	def stop(self, ipr):
		# Find the bridge
		dev = ipr.link_lookup(ifname=self.name)[0]

		# Delete the bridge
		ipr.link("delete", index=dev, kind="bridge")

		cprint(self.name + ' removed', 'green', end='\n')



# ============================= #
#      Point-to-Point Link      #
# ============================= #

class Link:
	
	# Init
	def __init__(self, interface1, interface2):
		self.interface1 = interface1
		self.interface2 = interface2
	

	# Create the link
	def create(self, ipr, client):
		# Create veth link (ip link add dev i1_name type veth peer name i2_name
		ipr.link("add", ifname = self.interface1.get_name(), peer = self.interface2.get_name(), kind="veth")
		
		# Get the interfaces
		idx1 = ipr.link_lookup(ifname = self.interface1.get_name())[0]
		idx2 = ipr.link_lookup(ifname = self.interface2.get_name())[0]

		cprint("Link "  + self.interface1.get_net_ns() + " <-> " + self.interface2.get_net_ns() + ' created', 'green', end='\n')
		
		# Interface 1
		if isinstance(self.interface1, NodeInterface):
			# Put the interface in is name_space
			ipr.link('set', index=idx1, net_ns_fd = self.interface1.get_net_ns())

			# Get the host
			node1 = client.containers.get(self.interface1.get_node().get_name())

			# Activate interface 1 and assign ip address
			node1.exec_run("ip link set \"" + self.interface1.get_name() +"\" up")
			node1.exec_run("ip addr add " + self.interface1.get_address() +" dev " + self.interface1.get_name())

		
			


		# Interface 2
		if isinstance(self.interface2, NodeInterface):
			# Put the interface in is name_space
			ipr.link('set', index=idx2, net_ns_fd = self.interface2.get_net_ns())

			# Get the hosts
			node2 = client.containers.get(self.interface2.get_node().get_name())

			# Activate interface 2 and assign ip address
			node2.exec_run("ip link set \"" + self.interface2.get_name() +"\" up")
			node2.exec_run("ip addr add " + self.interface2.get_address() +" dev " + self.interface2.get_name())

		if isinstance(self.interface1, BridgeInterface):
			bridge_idx = ipr.link_lookup(ifname = self.interface1.get_bridge().get_name())[0]
			ipr.link("set", index=idx1, state="up")
			ipr.link("set", index=idx1, master=bridge_idx)

		if isinstance(self.interface2, BridgeInterface):
			bridge_idx = ipr.link_lookup(ifname = self.interface2.get_bridge().get_name())[0]
			ipr.link("set", index=idx2, state="up")
			ipr.link("set", index=idx2, master=bridge_idx)

		

		

		
	#def remove(self, ipr):
	#	idx1 = ipr.link_lookup(ifname = self.interface1.get_name())[0]
	#	idx2 = ipr.link_lookup(ifname = self.interface2.get_name())[0]
	#	ipr.link("del", ifname = self.interface1.get_name(), peer = self.interface2.get_name(), kind="veth")
	#	cprint("Link "  + self.interface1.get_net_ns() + " <-> " + self.interface2.get_net_ns() + ' removed', 'green', end='\n')



# ===================== #
#      Interfaces       #
# ===================== #

class Interface:
	
	# Init
	def __init__(self, name, address, net_ns):
		self.name = name
		self.address = address
		self.net_ns = net_ns
		
	# Getters
	def get_name(self):
		return self.name

	def get_net_ns(self):
		return self.net_ns

	def get_address(self):
		return self.address

class NodeInterface(Interface):

	def __init__(self, name, node, address, net_ns):
		super().__init__(name, address, net_ns)
		self.node = node
		self.node.interfaces.append(self)

	def get_node(self):
		return self.node

class BridgeInterface(Interface):

	def __init__(self, name, bridge, address, net_ns):
		super().__init__(name, address, net_ns)
		self.bridge = bridge
		self.bridge.interfaces.append(self)

	def get_bridge(self):
		return self.bridge


# ========================== #
#      Node (Container)      #
# ========================== #

class Node:

	# Init
	def __init__(self, name, image, volume):
		self.name = name
		self.image = image
		self.volume = volume
		self.interfaces = []


	# Get Name
	def get_name(self):
		return self.name
	

	# Start the Node / Container
	def start(self, client, client_api):
		
		# Container with volume
		if not (self.volume is None): 
			# Local path of the volume (host fs)
			local_volume_path = self.volume[0]
			
			# Container path of the volume (container fs)
			container_volume_path = self.volume[1]

			# Run the container with the given image, name and volume
			client.containers.run(self.image, name=self.name, volumes={local_volume_path : {'bind': container_volume_path, 'mode':'rw'}}, privileged=True, detach=True)
		
		# Container without volume
		else :
			# Run the container with the given image and name
			client.containers.run(self.image, name=self.name, privileged=True, detach=True)
		
		# Get the container
		inspect = client_api.inspect_container(self.name)

		# Get container's pid
		pid = inspect['State']['Pid']

		# For Docker/Netns networking
		if not os.path.exists("/var/run/netns"):
			os.makedirs("/var/run/netns")

		# os.makedirs("/var/run/netns")

		if os.path.exists("/var/run/netns/"+self.name):
			os.remove("/var/run/netns/"+self.name)



		os.symlink("/proc/" + str(pid) + "/ns/net", "/var/run/netns/"+self.name)

		cprint(self.name + ' started', 'green', end='\n')
	

	# Open a terminal linked to the host (TODO)
	def open_terminal(self, client):
		cmd = "docker exec -it " + self.name + " /bin/bash"
		subprocess.call(['gnome-terminal', '-x', cmd])
		# p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		# client.containers.get(self.name).exec_run("/bin/bash", tty =True)
	

	# Stop and remove the host
	def stop(self, client):
		client.containers.get(self.name).stop(timeout=0)
		client.containers.get(self.name).remove()
		os.remove("/var/run/netns/"+self.name)
		cprint(self.name + ' stopped', 'green', end='\n')
		
