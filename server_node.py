# server_node.py
"""
A lightweight server node that simulates a cloud VM host.
Each node has:
 - a Flask API to handle VM/container creation requests
 - an internal scheduler that manages Docker containers
"""

from flask import Flask, jsonify, request, Response
import docker
import threading
import time
import argparse
import uuid
import queue
import subprocess


app = Flask(__name__)
client = docker.DockerClient(base_url='unix:///home/testuser/.docker/desktop/docker.sock')

# Internal store
containers = {}
lock = threading.Lock()

# Session store for interactive shells
shell_sessions = {}
shell_lock = threading.Lock()

@app.route("/create_vm", methods=["POST"])
def create_vm():
    """Create a lightweight container (simulating a VM)"""
    data = request.get_json(force=True)
    name = data.get("name", f"vm_{int(time.time())}")

    with lock:
        if name in containers:
            return jsonify({"error": "VM already exists"}), 400
        try:
            # Create a lightweight container using alpine Linux
            container = client.containers.run(
                "alpine",
                name=name,
                command="sleep infinity",
                detach=True,
                tty=True
            )
            containers[name] = container
            return jsonify({"status": "created", "name": name}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/list_vms", methods=["GET"])
def list_vms():
    """List all running containers (VMs)"""
    with lock:
        vms = [{"name": n, "id": c.short_id, "status": c.status} for n, c in containers.items()]
    return jsonify(vms)

@app.route("/delete_vm/<name>", methods=["DELETE"])
def delete_vm(name):
    """Stop and remove a container"""
    with lock:
        container = containers.pop(name, None)
        if not container:
            return jsonify({"error": "Not found"}), 404
        container.stop()
        container.remove()
    return jsonify({"status": "deleted", "name": name})

@app.route("/exec_vm/<name>", methods=["POST"])
def exec_vm(name):
    """Execute a command inside a container and stream output back."""
    data = request.get_json(force=True)
    cmd = data.get("cmd", "/bin/sh")

    with lock:
        container = containers.get(name)
        if not container:
            return jsonify({"error": "VM not found"}), 404

    try:
        exec_result = container.exec_run(cmd, stdin=False, tty=False)
        output = exec_result.output.decode("utf-8", errors="ignore")
        return Response(output, mimetype="text/plain")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/shell_session/<name>", methods=["POST"])
def shell_session(name):
    """Initiate an interactive shell session. Returns a session ID."""
    with lock:
        container = containers.get(name)
        if not container:
            return jsonify({"error": "VM not found"}), 404
    
    session_id = str(uuid.uuid4())
    
    try:
        # Create interactive exec instance
        exec_socket = container.exec_run(
            "/bin/sh",
            stdin=True,
            stdout=True,
            stderr=True,
            tty=True,
            socket=True,
            demux=False
        )
        
        with shell_lock:
            shell_sessions[session_id] = {
                "container_name": name,
                "socket": exec_socket,
                "created_at": time.time()
            }
        
        return jsonify({"session_id": session_id, "status": "active"}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/shell_input/<session_id>", methods=["POST"])
def shell_input(session_id):
    """Send input to an active shell session."""
    with shell_lock:
        session = shell_sessions.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
    
    data = request.get_json(force=True)
    cmd_input = data.get("input", "")
    
    try:
        socket = session["socket"]
        socket._sock.sendall((cmd_input + "\n").encode())
        return jsonify({"status": "sent"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/shell_output/<session_id>", methods=["GET"])
def shell_output(session_id):
    """Get output from an active shell session."""
    with shell_lock:
        session = shell_sessions.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
    
    try:
        socket = session["socket"]
        # Try to read with a short timeout
        socket._sock.settimeout(0.5)
        try:
            output = socket._sock.recv(4096).decode("utf-8", errors="ignore")
        except socket.timeout:
            output = ""
        socket._sock.settimeout(None)
        
        return Response(output, mimetype="text/plain")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/shell_close/<session_id>", methods=["POST"])
def shell_close(session_id):
    """Close an active shell session."""
    with shell_lock:
        session = shell_sessions.pop(session_id, None)
    
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    try:
        socket = session["socket"]
        socket._sock.close()
        return jsonify({"status": "closed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def auto_cleanup():
    """Scheduler thread to auto-remove stopped containers"""
    while True:
        with lock:
            for name, c in list(containers.items()):
                c.reload()
                if c.status != "running":
                    print(f"[Scheduler] Removing stopped container {name}")
                    containers.pop(name, None)
                    try:
                        c.remove(force=True)
                    except:
                        pass
        time.sleep(5)

if __name__ == "__main__":
    # --- parse the CLI port argument ---
    parser = argparse.ArgumentParser(description="Start a server node.")
    parser.add_argument("--port", type=int, default=5000,
                        help="Port number to run the server on (default: 5000)")
    args = parser.parse_args()

    # --- start background cleanup thread ---
    threading.Thread(target=auto_cleanup, daemon=True).start()

    # --- run Flask on the chosen port ---
    print(f"[+] Starting server node on port {args.port}")
    app.run(host="0.0.0.0", port=args.port)
