# API Documentation - Interactive SSH Endpoints

## Overview

The minicloud infrastructure now supports interactive SSH-like shell access to Docker containers. This document details all API endpoints available through the load balancer.

---

## Load Balancer Endpoints (Port 8000)

All endpoints go through the load balancer (`http://127.0.0.1:8000`)

### Existing Endpoints

#### Create VM
- **Method**: `POST`
- **Endpoint**: `/create_vm`
- **Request**:
  ```json
  {
    "name": "vm-name"
  }
  ```
- **Response** (201):
  ```json
  {
    "status": "created",
    "name": "vm-name"
  }
  ```

#### List All VMs
- **Method**: `GET`
- **Endpoint**: `/list_all`
- **Response** (200):
  ```json
  [
    {
      "http://127.0.0.1:5000": [
        {
          "name": "vm-1",
          "id": "a1b2c3d4",
          "status": "running"
        }
      ]
    }
  ]
  ```

#### Delete VM
- **Method**: `POST`
- **Endpoint**: `/delete_vm`
- **Request**:
  ```json
  {
    "server": "http://127.0.0.1:5000",
    "name": "vm-name"
  }
  ```
- **Response** (200):
  ```json
  {
    "status": "deleted",
    "name": "vm-name"
  }
  ```

---

## NEW: Interactive Shell Endpoints

### 1. Start Shell Session

**Initialize an interactive shell on a container**

- **Method**: `POST`
- **Endpoint**: `/shell_session`
- **Request**:
  ```json
  {
    "server": "http://127.0.0.1:5000",
    "name": "container-name"
  }
  ```
- **Response** (201):
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active"
  }
  ```
- **Timeout**: 30 seconds
- **Notes**: 
  - Session ID is unique per connection
  - Container must exist and be running
  - TTY mode is enabled for interactive input

### 2. Send Shell Input

**Send a command to an active shell session**

- **Method**: `POST`
- **Endpoint**: `/shell_input`
- **Request**:
  ```json
  {
    "server": "http://127.0.0.1:5000",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "input": "ls -la"
  }
  ```
- **Response** (200):
  ```json
  {
    "status": "sent"
  }
  ```
- **Timeout**: 10 seconds
- **Notes**:
  - Input is automatically followed by newline
  - No response output; poll `/shell_output` for results
  - Session must be active

### 3. Get Shell Output

**Poll for output from an active shell session**

- **Method**: `POST`
- **Endpoint**: `/shell_output`
- **Request**:
  ```json
  {
    "server": "http://127.0.0.1:5000",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
  ```
- **Response** (200):
  ```
  / # ls -la
  total 36
  drwxr-xr-x    1 root     root          4096 Nov 13 23:45 .
  drwxr-xr-x    1 root     root          4096 Nov 13 23:45 ..
  -rw-r--r--    1 root     root            12 Nov 13 23:45 .dockerenv
  ```
- **Timeout**: 5 seconds
- **Notes**:
  - Returns as plain text (mimetype: text/plain)
  - Non-blocking read (returns empty if no new data)
  - Must poll continuously for real-time output
  - Recommended polling interval: 100-200ms

### 4. Close Shell Session

**Terminate an active shell session**

- **Method**: `POST`
- **Endpoint**: `/shell_close`
- **Request**:
  ```json
  {
    "server": "http://127.0.0.1:5000",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
  ```
- **Response** (200):
  ```json
  {
    "status": "closed"
  }
  ```
- **Timeout**: 10 seconds
- **Notes**:
  - Closes the Docker exec socket
  - Removes session from memory
  - Safe to call even if session doesn't exist (returns 404 in that case)

---

## Server Node Endpoints (Port 5000/5001)

These endpoints are typically called by the load balancer, but can be called directly.

### New Shell Endpoints

**POST** `/shell_session/<name>`
- Initiates shell session on container named `<name>`
- Returns: Session ID and status

**POST** `/shell_input/<session_id>`
- Sends input to session
- Body: `{"input": "<command>"}`

**GET** `/shell_output/<session_id>`
- Gets output from session
- Returns: Raw text

**POST** `/shell_close/<session_id>`
- Closes session

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Missing server or name"
}
```

### 404 Not Found
```json
{
  "error": "VM not found"
}
```
or
```json
{
  "error": "Session not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "<error details>"
}
```

---

## Usage Examples

### Python Example

```python
import requests
import time

BASE = "http://127.0.0.1:8000"

# 1. Create VM
res = requests.post(f"{BASE}/create_vm", json={"name": "test-vm"})
print(res.json())

# 2. Start shell
res = requests.post(f"{BASE}/shell_session", 
                   json={"server": "http://127.0.0.1:5000", "name": "test-vm"})
session_id = res.json()["session_id"]

# 3. Send command
requests.post(f"{BASE}/shell_input",
             json={"server": "http://127.0.0.1:5000", 
                   "session_id": session_id,
                   "input": "ls -la"})

# 4. Get output
time.sleep(0.5)
res = requests.post(f"{BASE}/shell_output",
                   json={"server": "http://127.0.0.1:5000",
                         "session_id": session_id})
print(res.text)

# 5. Close session
requests.post(f"{BASE}/shell_close",
             json={"server": "http://127.0.0.1:5000",
                   "session_id": session_id})
```

### cURL Example

```bash
# Create VM
curl -X POST http://127.0.0.1:8000/create_vm \
  -H "Content-Type: application/json" \
  -d '{"name": "test-vm"}'

# Start shell
curl -X POST http://127.0.0.1:8000/shell_session \
  -H "Content-Type: application/json" \
  -d '{"server": "http://127.0.0.1:5000", "name": "test-vm"}'

# Send command
curl -X POST http://127.0.0.1:8000/shell_input \
  -H "Content-Type: application/json" \
  -d '{"server": "http://127.0.0.1:5000", "session_id": "550e8400...", "input": "pwd"}'

# Get output
curl -X POST http://127.0.0.1:8000/shell_output \
  -H "Content-Type: application/json" \
  -d '{"server": "http://127.0.0.1:5000", "session_id": "550e8400..."}'

# Close session
curl -X POST http://127.0.0.1:8000/shell_close \
  -H "Content-Type: application/json" \
  -d '{"server": "http://127.0.0.1:5000", "session_id": "550e8400..."}'
```

---

## Performance Characteristics

| Operation | Timeout | Latency | Notes |
|-----------|---------|---------|-------|
| Create Session | 30s | ~500ms | Docker exec setup |
| Send Input | 10s | ~100ms | Socket write |
| Get Output | 5s | ~100ms | Non-blocking read |
| Close Session | 10s | ~200ms | Cleanup |
| Poll Loop | - | ~100-200ms | Client responsibility |

---

## Thread Safety

- All shell sessions are protected by `shell_lock` (threading.Lock)
- Multiple concurrent sessions supported
- Load balancer handles routing to correct server
- Each server maintains independent session pool

---

## Session Lifecycle

```
1. POST /shell_session
   ├─ Create Docker exec socket
   ├─ Generate session_id (UUID)
   ├─ Store in shell_sessions[session_id]
   └─ Return session_id

2. Loop: Poll /shell_output
   ├─ Read from socket (non-blocking)
   └─ Return output or empty string

3. On Input: POST /shell_input
   ├─ Retrieve session
   ├─ Write to socket
   └─ Return status

4. POST /shell_close
   ├─ Retrieve session
   ├─ Close socket
   ├─ Remove from shell_sessions
   └─ Return status
```

---

## Limitations & Future Work

- **No authentication**: Add username/password or SSH keys
- **No session persistence**: Sessions lost on server restart
- **Polling only**: Consider WebSocket for real-time communication
- **Single shell**: Can't start multiple shells on same container
- **No file transfer**: Add SCP-like functionality
- **No session timeout**: Add automatic cleanup for idle sessions
- **No recording**: Session history not saved

---

## Debugging

Enable debug logging by modifying server_node.py:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check session status:
```python
# In server_node.py
with shell_lock:
    print(f"Active sessions: {shell_sessions.keys()}")
```

Monitor container output:
```bash
docker logs -f container-name
```
