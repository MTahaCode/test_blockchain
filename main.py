import subprocess, sys, requests
from urllib.parse import urlparse
from clients import Clients

def is_healthy(client):
    try:
        response = requests.get(f"{client.url}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

for client in Clients:
    if is_healthy(client):
        print(f"{client.name} is already healthy, skipping")
        continue

    print(f"{client.name} is not healthy, starting it")
    port = urlparse(client.url).port
    subprocess.Popen(
        ["cmd", "/k", sys.executable, "node.py", client.name, str(port)],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
