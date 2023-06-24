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