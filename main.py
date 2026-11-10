import subprocess, sys
from urllib.parse import urlparse
from clients import Clients

for client in Clients:
    port = urlparse(client.value).port
    subprocess.Popen(
        ["cmd", "/k", sys.executable, "node.py", client.name, str(port)],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
