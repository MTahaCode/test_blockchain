import logging

_client_name = ""

def setup_logger(client_name):
    global _client_name
    _client_name = client_name

    # Hide werkzeug's per-request lines, errors still show
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

def log(message):
    print(f"[{_client_name}] {message}")

def short(block_hash):
    return block_hash[:8]

def log_chain(hashes):
    log(f"  chain: {' · '.join(short(h) for h in hashes)}")
