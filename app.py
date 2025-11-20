"""MiniCloud Web App

Single app that:
- Auto-starts load balancer and server nodes (captures logs)
- User login/register for VM management
- Admin panel (admin/admin) to view logs
- Uses existing load_balancer.py and server_node.py

Run: python3 app.py
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import json
import os
import requests
import subprocess
import threading
import time
import queue
from pathlib import Path
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'minicloud-secret-key'

LB_URL = "http://127.0.0.1:8000"
USERS_FILE = Path("users.json")
VMS_FILE = Path("user_vms.json")

# Global log storage (thread-safe list)
log_storage = []
log_lock = __import__("threading").Lock()

lb_process = None
server_processes = []


def log_message(source, msg):
    """Add a message to the log storage."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] [{source}] {msg}"
    with log_lock:
        log_storage.append(full_msg)
    print(full_msg)  # Also print to console


def start_services():
    """Start load balancer and server nodes, capture their output."""
    global lb_process, server_processes
    
    log_message("APP", "Starting services...")
    
    try:
        # Start load balancer
        log_message("APP", "Starting load balancer on port 8000...")
        lb_process = subprocess.Popen(
            ["python3", "load_balancer.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        def read_lb_output():
            for line in lb_process.stdout:
                log_message("LB", line.strip())
            for line in lb_process.stderr:
                log_message("LB-ERR", line.strip())
        
        threading.Thread(target=read_lb_output, daemon=True).start()
        
        # Start server nodes
        for port in [5000, 5001]:
            log_message("APP", f"Starting server node on port {port}...")
            proc = subprocess.Popen(
                ["python3", "server_node.py", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            server_processes.append(proc)
            
            def read_server_output(p=proc, port=port):
                for line in p.stdout:
                    log_message(f"SERVER:{port}", line.strip())
                for line in p.stderr:
                    log_message(f"SERVER:{port}-ERR", line.strip())
            
            threading.Thread(target=read_server_output, daemon=True).start()
        
        log_message("APP", "All services started successfully!")
        time.sleep(2)  # Give them time to boot
    
    except Exception as e:
        log_message("APP-ERR", f"Failed to start services: {e}")


def get_recent_logs(n=100):
    """Get recent log messages."""
    with log_lock:
        return log_storage[-n:] if log_storage else []


# User management
def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE) as f:
            return json.load(f)
    return {"admin": "admin"}  # Default admin


def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)


def load_user_vms():
    if VMS_FILE.exists():
        with open(VMS_FILE) as f:
            return json.load(f)
    return {}


def save_user_vms(vms):
    with open(VMS_FILE, 'w') as f:
        json.dump(vms, f, indent=2)


# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password required', 'error')
            return redirect(url_for('register'))
        
        users = load_users()
        if username in users:
            flash('User already exists', 'error')
            return redirect(url_for('register'))
        
        users[username] = password
        save_users(users)
        flash('Registered! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        users = load_users()
        if username not in users or users[username] != password:
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))
        
        session['username'] = username
        session['is_admin'] = (username == 'admin')
        session.modified = True
        
        if username == 'admin':
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('login'))


@app.route('/delete-account', methods=['POST'])
def delete_account():
    """Delete current user account."""
    if not session.get('username') or session.get('is_admin'):
        flash('Cannot delete admin account', 'error')
        return redirect(url_for('dashboard'))
    
    username = session.get('username')
    confirm = request.form.get('confirm', '').lower()
    
    if confirm != 'yes':
        flash('Please confirm by typing YES', 'error')
        return redirect(url_for('dashboard'))
    
    # Delete user from users.json
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
    
    # Delete user's VMs from user_vms.json
    user_vms = load_user_vms()
    if username in user_vms:
        del user_vms[username]
        save_user_vms(user_vms)
    
    session.clear()
    flash('Account deleted successfully', 'success')
    return redirect(url_for('login'))


@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('login'))
    
    logs = get_recent_logs(200)
    return render_template('admin.html', logs=logs)


@app.route('/admin/logs')
def admin_logs_json():
    """API endpoint to fetch logs (for real-time updates)."""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    logs = get_recent_logs(100)
    return jsonify({'logs': logs})


@app.route('/')
def dashboard():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if session.get('is_admin'):
        return redirect(url_for('admin_panel'))
    
    username = session['username']
    user_vms = load_user_vms().get(username, {})
    
    return render_template('dashboard.html', username=username, user_vms=user_vms)


@app.route('/create-vm', methods=['POST'])
def create_vm():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    username = session['username']
    name = request.form.get('name', '').strip()
    
    if not name:
        flash('VM name required', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        r = requests.post(f"{LB_URL}/create_vm", json={'name': name}, timeout=10)
        if r.status_code == 201:
            # Query BOTH servers directly to find which one has the VM
            servers = ["http://127.0.0.1:5000", "http://127.0.0.1:5001"]
            
            user_vms = load_user_vms()
            if username not in user_vms:
                user_vms[username] = {}
            
            # Check both servers
            for srv_url in servers:
                try:
                    list_r = requests.get(f"{srv_url}/list_vms", timeout=5)
                    if list_r.status_code == 200:
                        vms = list_r.json()
                        if isinstance(vms, list):
                            for vm in vms:
                                if vm['name'] == name:
                                    user_vms[username][name] = {
                                        'server': srv_url,
                                        'created_at': datetime.now().isoformat(),
                                        'status': 'running'
                                    }
                                    save_user_vms(user_vms)
                                    flash(f'VM {name} created!', 'success')
                                    return redirect(url_for('dashboard'))
                except:
                    pass
            
            # If we get here, VM was created but not found - add it anyway with unknown server
            user_vms[username][name] = {
                'server': 'http://127.0.0.1:5000',  # Default to first server
                'created_at': datetime.now().isoformat(),
                'status': 'running'
            }
            save_user_vms(user_vms)
            flash(f'VM {name} created (using default server)', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'Failed to create VM: {r.json()}', 'error')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/delete-vm/<name>', methods=['POST'])
def delete_vm(name):
    if not session.get('username'):
        return redirect(url_for('login'))
    
    username = session['username']
    user_vms = load_user_vms()
    
    if username not in user_vms or name not in user_vms[username]:
        flash('VM not found', 'error')
        return redirect(url_for('dashboard'))
    
    vm_info = user_vms[username][name]
    server = vm_info['server']
    
    try:
        r = requests.post(f"{LB_URL}/delete_vm", json={'server': server, 'name': name}, timeout=10)
        if r.status_code == 200:
            del user_vms[username][name]
            save_user_vms(user_vms)
            flash(f'VM {name} deleted', 'success')
        else:
            flash(f'Failed to delete: {r.json()}', 'error')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/shutdown-vm/<name>', methods=['POST'])
def shutdown_vm(name):
    if not session.get('username'):
        return redirect(url_for('login'))
    
    flash('Shutdown feature not yet implemented', 'warning')
    return redirect(url_for('dashboard'))


@app.route('/shell/<name>')
def shell_page(name):
    if not session.get('username'):
        return redirect(url_for('login'))
    
    username = session['username']
    user_vms = load_user_vms()
    
    if username not in user_vms or name not in user_vms[username]:
        flash('VM not found', 'error')
        return redirect(url_for('dashboard'))
    
    vm_info = user_vms[username][name]
    server = vm_info['server']
    
    # Start shell session
    try:
        r = requests.post(f"{LB_URL}/shell_session", json={'server': server, 'name': name}, timeout=15)
        if r.status_code == 201:
            session_data = r.json()
            session['shell_session_id'] = session_data.get('session_id')
            session['shell_server'] = server
            session['shell_name'] = name
            session['shell_output'] = ''
            session.modified = True
            return render_template('shell.html', name=name, server=server)
        else:
            flash(f'Failed to start shell: {r.json()}', 'error')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/shell-input', methods=['POST'])
def shell_input():
    if not session.get('shell_session_id'):
        return jsonify({'error': 'No session'}), 400
    
    command = request.form.get('command', '').strip()
    
    if command.lower() == 'exit':
        try:
            requests.post(f"{LB_URL}/shell_close", json={
                'server': session['shell_server'],
                'session_id': session['shell_session_id']
            }, timeout=10)
        except:
            pass
        session.pop('shell_session_id', None)
        session.modified = True
        return redirect(url_for('dashboard'))
    
    try:
        requests.post(f"{LB_URL}/shell_input", json={
            'server': session['shell_server'],
            'session_id': session['shell_session_id'],
            'input': command
        }, timeout=10)
    except:
        pass
    
    session['shell_output'] = session.get('shell_output', '') + f"\n$ {command}\n"
    session.modified = True
    
    return redirect(url_for('shell_page', name=session['shell_name']))


@app.route('/shell-output')
def shell_output():
    if not session.get('shell_session_id'):
        return ""
    
    try:
        r = requests.post(f"{LB_URL}/shell_output", json={
            'server': session['shell_server'],
            'session_id': session['shell_session_id']
        }, timeout=3)
        if r.status_code == 200:
            # Get accumulated history and add new output
            current = session.get('shell_output', '')
            new_text = r.text
            # Only add if it's not empty and not just the prompt
            if new_text and new_text.strip() and new_text not in current:
                current += new_text
                session['shell_output'] = current
                session.modified = True
            return current
    except Exception as e:
        pass
    
    return session.get('shell_output', '')


if __name__ == '__main__':
    # Start services in background
    threading.Thread(target=start_services, daemon=True).start()
    
    print("\n" + "="*60)
    print("MiniCloud Web App")
    print("="*60)
    print("\nAdmin login: admin / admin")
    print("User registration: available at /register")
    print("\nStarting Flask on http://127.0.0.1:5555")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5555, debug=False)
