from flask import Flask, jsonify, request
import sys, traceback, requests
from werkzeug.exceptions import HTTPException
from blockchain import BlockChain, Block
from clients import Clients

client_name = sys.argv[1]
port = int(sys.argv[2])

blockchain = BlockChain()

app = Flask(__name__)

@app.errorhandler(Exception)
def handle_error(error):
    status = error.code if isinstance(error, HTTPException) else 500
    print(f"[{client_name}] {request.method} {request.path} failed with {status}: {error}")

    if status == 500:
        traceback.print_exception(error)

    return jsonify({"error": str(error)}), status

@app.get("/health")
def health():
    print(f"[{client_name}] /health called")
    return jsonify({"message": f"{client_name} is healthy"})

@app.get("/chain")
def chain():
    print(f"[{client_name}] /chain called, length {len(blockchain.chain)}")
    return jsonify(blockchain.getJson())

@app.post("/add-block")
def add_block():
    body = request.get_json(silent=True)
    print(f"[{client_name}] /add-block called with body: {body}")

    if not body or "block" not in body:
        print(f"[{client_name}] /add-block rejected: block not in body")
        return jsonify({"message": "Block not in body"})

    new_block = blockchain.add_block(body["block"])
    print(f"[{client_name}] Added block {new_block.index}, hash {new_block.hash}")

    for client in Clients:
        if client.name == client_name:
            continue
        
        client_url = client.value

        print(f"[{client_name}] Sending block {new_block.index} to {client.name}")
        try:
            response = requests.post(f"{client_url}/validate", json={"block" : new_block.getJson()})
            print(f"[{client_name}] {client.name} responded with {response.status_code}: {response.text.strip()}")
        except requests.RequestException as error:
            print(f"[{client_name}] Could not reach {client.name}: {error}")

    return jsonify("Block Added Successfully.")

@app.post("/validate")
def validate():
    body = request.get_json(silent=True)
    print(f"[{client_name}] /validate called with body: {body}")

    if not body or "block" not in body:
        print(f"[{client_name}] /validate rejected: block not in body")
        return jsonify({"message": "Block not in body"})

    block = Block(**body["block"])

    if Block.calculate_hash(block.index, block.timestamp, block.data, block.prev_hash) != block.hash:
        print(f"[{client_name}] /validate rejected: incorrect hash")
        return jsonify({"message" : "Incorrect hash"})

    latest_local_block = blockchain.chain[-1]

    if latest_local_block.index + 1 != block.index:
        print(f"[{client_name}] /validate rejected: expected index {latest_local_block.index + 1}, got {block.index}")
        return jsonify({"message" : "Old Block"})

    if latest_local_block.hash != block.prev_hash:
        print(f"[{client_name}] /validate rejected: prev_hash {block.prev_hash} doesn't match latest hash {latest_local_block.hash}")
        return jsonify({"message" : "New Block previous hash doesn't equal latest block"})

    blockchain.add_received_block(block)
    print(f"[{client_name}] /validate accepted block {block.index}")
    return jsonify({"message": "Block accepted"})

def sync_chain_from_peer():
    for client in Clients:
        if client.name == client_name:
            continue

        try:
            response = requests.get(f"{client.value}/chain", timeout=3)
        except requests.RequestException:
            print(f"[{client_name}] {client.name} not running, starting with own chain")
            continue

        blockchain.load_chain([Block(**block) for block in response.json()])
        print(f"[{client_name}] Joined late, copied chain from {client.name}, length {len(blockchain.chain)}")
        return

if __name__ == "__main__":
    sync_chain_from_peer()
    print(f"{client_name} is active")
    app.run(port=port, debug=True)
