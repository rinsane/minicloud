# Quick Start Guide - Interactive SSH Support

## Installation & Setup

1. **Ensure Docker is running** on your system
2. **Verify Python 3.10+** is installed:
   ```bash
   python3 --version
   ```

3. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

## Running the System

### Terminal 1 - Load Balancer
```bash
python3 load_balancer.py
# Output: Running on http://0.0.0.0:8000
```

### Terminal 2 - Server Nodes (node 1)
```bash
python3 server_node.py --port 5000
# Output: [+] Starting server node on port 5000
```

### Terminal 3 - Server Nodes (node 2)
```bash
python3 server_node.py --port 5001
# Output: [+] Starting server node on port 5001
```

### Terminal 4 - Client CLI
```bash
python3 client.py
# Interactive menu will appear
```

## Using the Interactive Shell

### Step-by-Step Example

1. **Launch client** and see menu:
   ```
   ========== Mini Cloud Client ==========
   1. Create VM
   2. List VMs
   3. SSH (exec) into VM
   4. Delete VM
   5. Exit
   =======================================
   ```

2. **Create a VM** (option 1):
   ```
   Enter new VM name: my-test-vm
   Response: {'status': 'created', 'name': 'my-test-vm'}
   ```

3. **Connect to VM** (option 3):
   ```
   Enter VM name to open shell: my-test-vm
   [+] Opening interactive shell to my-test-vm on http://127.0.0.1:5000...
   [+] Session started (ID: a1b2c3d4...)
   [+] Type 'exit' to close connection.
   
   / #
   ```

4. **Run commands** in the shell:
   ```
   / # ls -la
   total 36
   drwxr-xr-x    1 root     root          4096 Nov 13 2025 .
   drwxr-xr-x    1 root     root          4096 Nov 13 2025 ..
   ...
   
   / # uname -a
   Linux 7f8e9d0c1b2a 6.1.89-1-generic #1 SMP PREEMPT_DYNAMIC
   
   / # echo "Hello from container!"
   Hello from container!
   
   / # exit
   [+] Closing connection...
   ```

## What's New

### Key Features

✅ **Interactive Shell Sessions** - Full bidirectional communication with containers
✅ **Real-time I/O** - See command output instantly as it happens
✅ **Session Management** - Unique session IDs for multiple connections
✅ **Graceful Shutdown** - Clean connection closure with "exit" command
✅ **Keyboard Interrupt** - Ctrl+C support
✅ **Thread-safe** - Handles concurrent operations safely

### Technical Improvements

- **Non-blocking Socket Reads** - Prevents terminal lag
- **Daemon Threads** - Automatic cleanup on exit
- **Error Handling** - Timeout recovery and exception management
- **Polling Architecture** - Compatible with REST constraints

## Architecture

```
┌─────────────┐
│   Client    │ (Python + REST)
│   Terminal  │
└──────┬──────┘
       │
       ├─ POST /shell_session ──→ Start session
       ├─ POST /shell_input   ──→ Send commands
       ├─ GET  /shell_output  ──→ Poll output (continuous)
       └─ POST /shell_close   ──→ End session
       │
       ▼
┌──────────────────┐
│  Load Balancer   │ (Port 8000)
│ (Round-robin)    │
└──────┬───────────┘
       │
       ├──────────────────┬──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
   ┌────────┐         ┌────────┐        
   │Server 1│         │Server 2│        
   │Port    │         │Port    │        
   │5000    │         │5001    │        
   └────┬───┘         └────┬───┘        
        │                  │
        └──────┬───────────┘
               │
               ▼
        ┌─────────────┐
        │   Docker    │
        │ Containers  │
        │  (Alpine)   │
        └─────────────┘
```

## Troubleshooting

### Problem: Connection times out
- **Solution**: Ensure all servers are running (check all terminal windows)
- **Check**: `curl http://127.0.0.1:8000/list_all`

### Problem: "Session not found" error
- **Solution**: Session may have expired (5+ min of inactivity)
- **Workaround**: Reconnect to the container

### Problem: Commands not executing
- **Solution**: Check container is running via option 2 (List VMs)
- **Check**: Look for "running" status in the list

### Problem: "Docker socket not found"
- **Solution**: Update the Docker socket path in `server_node.py` (line ~17)
- **Common paths**:
  - Linux: `/var/run/docker.sock`
  - Mac Docker Desktop: `/Users/<user>/.docker/run/docker.sock`
  - WSL: `/var/run/docker.sock`

## Performance Notes

- **Polling Interval**: 100ms (10 requests/sec maximum)
- **Output Timeout**: 500ms socket read timeout
- **Session Cleanup**: Automatic when connection closes
- **Concurrent Sessions**: Supported (one per user, managed by load balancer)

## Next Steps / Future Enhancements

- [ ] True SSH with public key authentication
- [ ] SCP-like file transfer
- [ ] Session logging/recording
- [ ] Tab completion support
- [ ] Command history persistence
- [ ] WebSocket upgrade for lower latency
- [ ] Multi-user session sharing
