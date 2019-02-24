# Network Simulator
A Docker-based network simulator.

### 1. Prerequisites:
[Docker](https://www.docker.com/)  
[Python](https://www.python.org/)

Python libraries:  
* [docker](https://pypi.org/project/docker/)  
* [pyroute2](https://pypi.org/project/pyroute2/)  
* [pyyaml](https://pypi.org/project/PyYAML/)  
* [termcolor](https://pypi.org/project/termcolor/)  

### 2. Usage:
You must be root to run the following commands.  
**Start a network**  
```
python3 netsim.py start Networks/network.yaml
```
**Stop a network**
```
python3 netsim.py stop Networks/network.yaml
```

### 3. Network file:
#### Example:
```
network:
    name: example_network
    
    hosts:
        - name: host1
          image: apache
          volume: 
            - /home/user/Docker/apache1/html/
            - /var/www/html/

        - name: host2
          image: apache
          volume: 
            - /home/user/Docker/apache2/html/
            - /var/www/html/

        - name: host3
          image: apache
    
    links:
        - host1:v0:10.0.0.1/24-host2:v0:10.0.0.2/24
        - host1:v1:10.0.1.1/24-host3:v0:10.0.1.3/24
```
