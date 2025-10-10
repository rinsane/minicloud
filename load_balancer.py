"""
Simple load balancer that distributes requests between two servers.
"""

from flask import Flask, request, jsonify
import requests
import itertools

app = Flask(__name__)

# backend servers (for now, 2)
servers = ["http://127.0.0.1:5000", "http://127.0.0.1:5001"]
server_cycle = itertools.cycle(servers)


@app.route("/create_vm", methods=["POST"])
def create_vm():
    """Forward the request to one of the backend servers."""
    server = next(server_cycle)
    try:
        res = requests.post(f"{server}/create_vm", json=request.get_json(force=True), timeout=15)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/list_all", methods=["GET"])
def list_all():
    """Fetch list of VMs from all servers."""
    results = []
    for s in servers:
        try:
            r = requests.get(f"{s}/list_vms", timeout=5)
            results.append({s: r.json()})
        except Exception as e:
            results.append({s: f"Error: {e}"})
    return jsonify(results)


@app.route("/delete_vm", methods=["POST"])
def delete_vm():
    """Forward delete requests to the server that owns the container."""
    data = request.get_json(force=True)
    server = data.get("server")
    name = data.get("name")
    if not server or not name:
        return jsonify({"error": "Missing server or name"}), 400

    try:
        res = requests.delete(f"{server}/delete_vm/{name}", timeout=15)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/exec_vm", methods=["POST"])
def exec_vm():
    """Forward exec (SSH-like) requests to the correct server."""
    data = request.get_json(force=True)
    server = data.get("server")
    name = data.get("name")
    cmd = data.get("cmd", "/bin/sh")
    if not server or not name:
        return jsonify({"error": "Missing server or name"}), 400

    try:
        res = requests.post(f"{server}/exec_vm/{name}", json={"cmd": cmd}, timeout=15)
        return (res.text, res.status_code, {"Content-Type": "text/plain"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

