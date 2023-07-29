import subprocess
import json
import docker


def get_acr_access_token(acr_name):
    cmd = f"az acr login --name {acr_name} --expose-token --output json"
    result = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if result.returncode == 0:
        token_output = json.loads(result.stdout)
        access_token = token_output["accessToken"]

        return access_token
    else:
        raise Exception(
            f"Failed to get ACR access token. Error: {result.stderr}")


def docker_login(acr_name, username, password):
    docker_client = docker.from_env()

    docker_client.login(
        username=username,
        password=password,
        registry="containerizationtool.azurecr.io"
    )


if __name__ == "__main__":
    ACR_NAME = "containerizationtool"

    try:
        access_token = get_acr_access_token(ACR_NAME)
        print("Access Token:", access_token)

        # Perform Docker login using the token
        docker_login(
            ACR_NAME, "00000000-0000-0000-0000-000000000000", access_token)
    except Exception as e:
        print("Error:", str(e))
