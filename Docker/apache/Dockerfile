FROM debian:jessie-slim
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y iptables iproute2 net-tools telnet iputils-ping apache2

EXPOSE 80
CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
