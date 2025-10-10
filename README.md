# Mini Cloud Infrastructure (Python + Docker)

This project simulates a mini cloud environment on local or distributed machines.
It implements lightweight server nodes, a load balancer, and a client CLI to manage virtual "VMs" (Docker containers) that can be created, listed, deleted, and accessed via SSH.

---

## Architecture Overview

```
CLIENT  ->  LOAD BALANCER  ->  SERVER NODE(S)  ->  DOCKER CONTAINERS
```

* **Client** – CLI that sends REST calls to the Load Balancer
* **Load Balancer** – Distributes requests between servers (round-robin)
* **Server Node** – Hosts and manages containers (acts like a VM host)
* **Container (VM)** – Lightweight Alpine Linux instance with SSH access

---

## Prerequisites

* Linux / WSL with Python 3.10+
* Docker Desktop or native Docker Engine

  * Docker socket: `unix:///home/<user>/.docker/desktop/docker.sock`
* Python packages:

  ```bash
  pip install flask requests docker
  ```

---

## Setup & Run

### 1. Start Server Nodes

Each server simulates a compute host.

```bash
python3 server_node.py --port 5000
python3 server_node.py --port 5001
```

Each server connects to your Docker Desktop daemon
(`unix:///home/testuser/.docker/desktop/docker.sock`).

---

### 2. Start Load Balancer

```bash
python3 load_balancer.py
```

* Runs on port 8000
* Forwards `/create_vm`, `/delete_vm`, `/exec_vm`, `/list_all` between servers

---

### 3. Launch Client

```bash
python3 client.py
```

#### Available Operations

| Option | Description                                                      |
| ------ | ---------------------------------------------------------------- |
| 1      | Create VM - starts a container on one of the servers             |
| 2      | List VMs - shows all containers across servers                   |
| 3      | SSH into VM - opens shell (real SSH if enabled, or exec command) |
| 4      | Delete VM - stops and removes container                          |
| 5      | Exit - close client                                              |

---

## VM (Container) Details

* Base image: `alpine-ssh` (Alpine + OpenSSH)
* Runs `sshd -D`
* Exposes port 22/tcp (mapped dynamically on host)
* Server returns:

  ```json
  {
    "status": "created",
    "name": "vm_1",
    "ssh_host": "192.168.1.10",
    "ssh_port": "32775",
    "username": "root",
    "password": "root"
  }
  ```
* Connect directly:

  ```bash
  ssh root@<ssh_host> -p <ssh_port>
  ```

---

## Auto-Cleanup

Each server runs a background scheduler thread that:

* Monitors stopped containers
* Removes stale entries automatically

---

## Design Summary

| Component          | Language           | Responsibility                            |
| ------------------ | ------------------ | ----------------------------------------- |
| `client.py`        | Python (CLI)       | User interface - sends API calls          |
| `load_balancer.py` | Flask              | Routes and balances requests across nodes |
| `server_node.py`   | Flask + Docker SDK | Manages lifecycle of containers ("VMs")   |
| Containers         | Docker             | Lightweight Linux instances (can SSH in)  |

---

## Example Flow

```bash
python3 client.py
# 1 -> create VM (load balanced)
# 2 -> list all
# 3 -> ssh into any VM (ssh root@server -p <port>)
# 4 -> delete VM
```

---

**Result:**
A functional mini-cloud capable of spinning up isolated, SSH-accessible lightweight "VMs," balanced across multiple servers using Python and Docker.

