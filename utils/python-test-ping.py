import subprocess

def ping_google_dns():
    try:
        # Run the ping command with subprocess
        subprocess.run(["ping", "8.8.8.8"], check=True)
    except subprocess.CalledProcessError:
        print("Ping request failed.")

if __name__ == "__main__":
    ping_google_dns()
