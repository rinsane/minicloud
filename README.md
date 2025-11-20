# Mini Cloud Infrastructure (Python + Docker)

This project simulates a mini cloud environment on local or distributed machines.
It implements lightweight server nodes, a load balancer, and a web dashboard to manage virtual "VMs" (Docker containers) that can be created, listed, deleted, and accessed via SSH.

---

## Architecture Overview

```
WEB APP (Flask)  ->  LOAD BALANCER  ->  SERVER NODE(S)  ->  DOCKER CONTAINERS
```

* **Web App** (`app.py`) – Single Flask app that auto-starts services, provides user login/register, and admin panel with logs
* **Load Balancer** (`load_balancer.py`) – Distributes requests between servers (round-robin)
* **Server Node** (`server_node.py`) – Hosts and manages containers (acts like a VM host)
* **Container (VM)** – Lightweight Alpine Linux instance with SSH access

---

## Prerequisites

* Linux / WSL with Python 3.10+
* Docker Desktop or native Docker Engine
* Python packages: `flask requests docker`

---

## Quick Start

```bash
# Install dependencies
pip install flask requests docker

# Run the app (auto-starts services)
python3 app.py
```

Then open http://127.0.0.1:5555 in your browser.

### Default Credentials

* **Admin**: `admin` / `admin` (see system logs)
* **Register**: Create your own user account

---

## Features

### User Dashboard
* Create VMs
* List your VMs
* SSH into VM (shell terminal in browser)
* Shutdown VM (graceful stop)
* Delete VM (permanent removal)

### Admin Panel
* View real-time logs from all services (load balancer, server nodes)
* Monitor system activity

---

## VM Details

* Base image: `alpine` (lightweight Linux)
* Runs in Docker containers
* Exposes port 22/tcp for SSH (optional)
* SSH via shell interface in dashboard

---

## How It Works

1. **App starts** → automatically launches load balancer and 2 server nodes on ports 5000/5001
2. **User login/register** → credentials stored locally
3. **Create VM** → load balancer assigns to a server, container created
4. **SSH into VM** → starts interactive shell session via Docker exec
5. **Shutdown VM** → container pauses (can be restarted)
6. **Delete VM** → container permanently removed
7. **Admin panel** → see all logs from all services

---

## API Endpoints (for reference)

* `POST /create_vm` – Create a container
* `GET /list_all` – List VMs on a server (round-robin)
* `POST /delete_vm` – Delete a container
* `POST /shutdown_vm` – Stop a container (graceful)
* `POST /shell_session` – Start interactive shell
* `POST /shell_input` – Send command to shell
* `POST /shell_output` – Get shell output
* `POST /shell_close` – Close shell session

---

## File Structure

```
.
├── app.py                    # Main Flask app (user login, dashboard, admin)
├── load_balancer.py         # Load balancer (round-robin)
├── server_node.py           # Server node (container host)
├── client.py                # Old CLI (deprecated)
├── templates/
│   ├── login.html           # Login page
│   ├── register.html        # Register page
│   ├── dashboard.html       # User dashboard
│   ├── admin.html           # Admin logs
│   └── shell.html           # Terminal shell
├── users.json               # User credentials (auto-created)
├── user_vms.json            # User VM registry (auto-created)
└── requirements.txt         # Python dependencies
```

---

## Troubleshooting

### "Failed to connect to Docker daemon"
- Ensure Docker Desktop is running or Docker daemon is active

### Services not starting
- Check logs in Admin panel for errors
- Verify ports 8000, 5000, 5001 are not in use

### Shell not responding
- Try refreshing the page
- Check Admin logs for errors

---

## Notes

* This is a demo/learning project, not production-ready
* Passwords are stored in plain text (for simplicity)
* Containers are created on the host Docker daemon
* All VM data persists in JSON files (users.json, user_vms.json)


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

