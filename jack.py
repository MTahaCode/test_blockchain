from flask import Flask, jsonify, request
import os


app = Flask(__name__)

filename = os.path.basename(__file__).split(".")[0]

@app.get("/health")
def health():
    return jsonify({"message": f"{filename} is healthy"})

if __name__ == "__main__":
    print(f"{filename} is active")
    app.run(port=5000, debug=True)

