import subprocess

def get_docker_nat_table(container_id):
    command = f"docker inspect --format='{{{{.State.Pid}}}}' {container_id}"
    pid = subprocess.check_output(command, shell=True, text=True).strip()

    command = f"nsenter --net=/proc/{pid}/ns/net iptables -t nat --list"
    output = subprocess.check_output(command, shell=True, text=True).strip()

    return output

# Usage example
container_id = "<your-container-id>"
nat_table = get_docker_nat_table(container_id)
print(nat_table)
