test_network_name=mynetwork

docker network create --driver bridge --opt com.docker.network.bridge.name="$test_network_name" "$test_network_name"