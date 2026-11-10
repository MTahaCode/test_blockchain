from flask import Flask, jsonify, request
import sys, traceback, requests
from werkzeug.exceptions import HTTPException
from blockchain import BlockChain, Block
from clients import Clients
from logger import setup_logger, log, short, log_chain

client_name = sys.argv[1]
port = int(sys.argv[2])
seed_blocks = Clients[client_name].seed_blocks

setup_logger(client_name)

blockchain = BlockChain()
blockchain.add_seed_blocks(seed_blocks)

app = Flask(__name__)

@app.errorhandler(Exception)
def handle_error(error):
    status = error.code if isinstance(error, HTTPException) else 500
    log(f"✗ {request.method} {request.path} failed with {status}: {error}")

    if status == 500:
        traceback.print_exception(error)

    return jsonify({"error": str(error)}), status

@app.get("/health")
def health():
    log("← /health")
    return jsonify({"message": f"{client_name} is healthy"})

@app.get("/chain")
def chain():
    log(f"← /chain (length {len(blockchain.chain)})")
    return jsonify(blockchain.getJson())

@app.get("/hashes")
def hashes():
    log(f"← /hashes (length {len(blockchain.chain)})")
    return jsonify(blockchain.get_hashes())

@app.get("/blocks-after/<block_hash>")
def blocks_after(block_hash):
    for index, block in enumerate(blockchain.chain):
        if block.hash == block_hash:
            blocks = blockchain.chain[index + 1:]
            log(f"← /blocks-after #{index} ({short(block_hash)}): sending {len(blocks)} blocks")
            return jsonify([b.getJson() for b in blocks])

    log(f"← /blocks-after {short(block_hash)}: not found")
    return jsonify({"message": "Hash not found"}), 404

@app.post("/add-block")
def add_block():
    body = request.get_json(silent=True)

    if not body or "block" not in body:
        log("✗ /add-block rejected: block not in body")
        return jsonify({"message": "Block not in body"})

    new_block = blockchain.add_block(body["block"])
    log(f"✓ added block #{new_block.index} \"{new_block.data}\" ({short(new_block.hash)})")
    log_chain(blockchain.get_hashes())

    for client in Clients:
        if client.name == client_name:
            continue

        log(f"→ block #{new_block.index} to {client.name}")
        try:
            response = requests.post(f"{client.url}/validate", json={"block" : new_block.getJson(), "sender": client_name})
            reply = response.json().get("message", response.text.strip()) if response.ok else response.status_code
            log(f"  {client.name}: {reply}")
        except requests.RequestException:
            log(f"  {client.name}: not reachable")

    return jsonify("Block Added Successfully.")

@app.post("/validate")
def validate():
    body = request.get_json(silent=True)

    if not body or "block" not in body:
        log("✗ /validate rejected: block not in body")
        return jsonify({"message": "Block not in body"})

    block = Block(**body["block"])
    sender = body.get("sender")
    log(f"← block #{block.index} from {sender}  ({short(block.hash)} → prev {short(block.prev_hash)})")

    if Block.calculate_hash(block.index, block.timestamp, block.data, block.prev_hash) != block.hash:
        log("✗ rejected: incorrect hash")
        return jsonify({"message" : "Incorrect hash"})

    latest_local_block = blockchain.chain[-1]

    # Case A: block isn't ahead of our chain, keep ours
    if block.index <= latest_local_block.index:
        log(f"✗ rejected: not ahead of our #{latest_local_block.index}")
        return jsonify({"message" : "Old Block"})

    # Case B: block fits right on top of our chain
    if block.index == latest_local_block.index + 1 and block.prev_hash == latest_local_block.hash:
        blockchain.add_received_block(block)
        log(f"✓ accepted block #{block.index}")
        log_chain(blockchain.get_hashes())
        return jsonify({"message": "Block accepted"})

    # Case C: block is ahead but doesn't fit, we're behind: get the missing blocks from the sender
    # Get the sender's hashes and find the newest block we both have
    sender_hashes = fetch_hashes(sender)
    ancestor = blockchain.find_common_ancestor(sender_hashes) if sender_hashes else None
    if ancestor is None:
        log(f"✗ rejected: no common ancestor with {sender}")
        return jsonify({"message" : "No common ancestor with sender"})

    log(f"⟳ behind {sender}, common ancestor #{ancestor.index}")
    branch = fetch_blocks_after(sender, ancestor.hash)

    if branch is None or not blockchain.is_valid_branch(branch):
        log(f"✗ rejected: couldn't catch up with {sender}")
        return jsonify({"message" : "Couldn't catch up with sender"})

    removed = len(blockchain.chain) - (ancestor.index + 1)
    blockchain.replace(branch)
    log(f"⟳ replaced after #{ancestor.index}: removed {removed}, added {len(branch)}")
    log_chain(blockchain.get_hashes())
    return jsonify({"message": "Caught up with sender"})

def fetch_hashes(sender):
    if sender not in Clients.__members__:
        log(f"  unknown sender {sender}, can't fetch hashes")
        return None

    try:
        response = requests.get(f"{Clients[sender].url}/hashes", timeout=3)
    except requests.RequestException:
        log(f"  {sender}: not reachable")
        return None

    return response.json()

def fetch_blocks_after(sender, block_hash):
    if sender not in Clients.__members__:
        log(f"  unknown sender {sender}, can't fetch blocks")
        return None

    try:
        response = requests.get(f"{Clients[sender].url}/blocks-after/{block_hash}", timeout=3)
    except requests.RequestException:
        log(f"  {sender}: not reachable")
        return None

    if response.status_code != 200:
        log(f"  {sender} doesn't have block {short(block_hash)}")
        return None

    return [Block(**block) for block in response.json()]

def sync_chain_from_peer():
    for client in Clients:
        if client.name == client_name:
            continue

        try:
            response = requests.get(f"{client.url}/chain", timeout=3)
        except requests.RequestException:
            log(f"  {client.name} not running, starting with own chain")
            continue

        blockchain.load_chain([Block(**block) for block in response.json()])
        log(f"⟳ joined late, copied chain from {client.name}")
        return

if __name__ == "__main__":
    if seed_blocks:
        log(f"seeded with {seed_blocks} blocks, skipping peer sync")
    else:
        sync_chain_from_peer()
    log(f"active on port {port}")
    log_chain(blockchain.get_hashes())
    app.run(port=port, debug=True)
