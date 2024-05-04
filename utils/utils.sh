# run ubuntu container
docker run -it --name my-ubuntu ubuntu

# inspect container ip
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my-ubuntu

# inspect container network
docker inspect my-ubuntu --format='{{json .NetworkSettings.Networks}}' | jq

# list dokcer networks
docker network ls

# inspect docker network
docker network inspect bridge

# dump docker network
sudo tcpdump -i docker0

# source virtualenv
source myenv/bin/activate

# show network interfaces
ip link show

# show iptables
docker exec -u root -it 8e80272f9e78 iptables -t nat -L

# run dokcer with NET_ADMIN capability
docker run -it --cap-add NET_ADMIN --network=mynetwork --name my-ubuntu my-ubuntu

# redirect traffic to localhost
iptables -t nat -A OUTPUT -d 8.8.8.8 -j DNAT --to-destination 9.9.9.9

# show iptables
iptables -t nat -L

# start contaier which logs to syslog
docker run \
    --log-driver=syslog \
    --log-opt syslog-format=rfc5424 \
    --log-opt syslog-address=tcp://localhost:5140 \
    test_image

# remove images that contains word http-server
docker rmi $(docker images | grep http-server | awk '{print $3}')