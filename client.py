"""
Pure HTTP client for the mini cloud.
No direct Docker access — all operations go through the load balancer.
"""

import requests
import sys
import time
import threading

LOAD_BALANCER = "http://127.0.0.1:8000"


def create_vm():
    name = input("Enter new VM name: ").strip()
    if not name:
        print("❌ VM name required.")
        return

    res = requests.post(f"{LOAD_BALANCER}/create_vm", json={"name": name}, timeout=30)
    print("Response:", res.json())


def list_vms():
    res = requests.get(f"{LOAD_BALANCER}/list_all", timeout=10)
    data = res.json()
    all_vms = []
    print("\n=== Running Containers (All Servers) ===")
    for srv in data:
        for server, vms in srv.items():
            print(f"\nServer: {server}")
            if isinstance(vms, list):
                for vm in vms:
                    print(f"  - {vm['name']} ({vm['id']}) [{vm['status']}]")
                    all_vms.append((server, vm["name"]))
            else:
                print(f"  ⚠️  {vms}")
    return all_vms


def delete_vm():
    all_vms = list_vms()
    if not all_vms:
        print("No VMs to delete.")
        return
    choice = input("\nEnter VM name to delete: ").strip()
    target = next(((s, n) for s, n in all_vms if n == choice), None)
    if not target:
        print("❌ VM not found.")
        return
    server, name = target
    res = requests.post(f"{LOAD_BALANCER}/delete_vm", json={"server": server, "name": name}, timeout=30)
    print("Response:", res.json())


def ssh_into_vm():
    all_vms = list_vms()
    if not all_vms:
        print("No VMs to connect.")
        return
    choice = input("\nEnter VM name to open shell: ").strip()
    target = next(((s, n) for s, n in all_vms if n == choice), None)
    if not target:
        print("❌ VM not found.")
        return
    server, name = target
    
    print(f"\n[+] Opening interactive shell to {name} on {server}...")
    
    # Initiate shell session
    try:
        res = requests.post(f"{LOAD_BALANCER}/shell_session", 
                          json={"server": server, "name": name}, 
                          timeout=30)
        if res.status_code != 201:
            print(f"❌ Failed to create shell session: {res.json()}")
            return
        
        session_data = res.json()
        session_id = session_data.get("session_id")
        print(f"[+] Session started (ID: {session_id[:8]}...)")
        print("[+] Type 'exit' to close connection.\n")
        
        # Open interactive shell
        interactive_shell(server, session_id)
    
    except Exception as e:
        print(f"❌ Error: {e}")


def interactive_shell(server, session_id):
    """Interactive shell session with live input/output."""
    
    # Start output reader thread
    output_buffer = []
    stop_event = threading.Event()
    
    def read_output():
        while not stop_event.is_set():
            try:
                res = requests.post(f"{LOAD_BALANCER}/shell_output", 
                                  json={"server": server, "session_id": session_id}, 
                                  timeout=1)
                if res.status_code == 200 and res.text:
                    print(res.text, end='', flush=True)
            except requests.exceptions.Timeout:
                pass
            except Exception as e:
                if not stop_event.is_set():
                    print(f"\n[!] Output reader error: {e}")
            time.sleep(0.05)
    
    reader_thread = threading.Thread(target=read_output, daemon=True)
    reader_thread.start()
    
    try:
        while True:
            user_input = input()
            
            if user_input.lower() == "exit":
                print("\n[+] Closing connection...")
                stop_event.set()
                break
            
            # Send input to shell
            try:
                res = requests.post(f"{LOAD_BALANCER}/shell_input", 
                                  json={"server": server, "session_id": session_id, "input": user_input}, 
                                  timeout=10)
                if res.status_code != 200:
                    print(f"[!] Error sending command: {res.json()}")
            except Exception as e:
                print(f"[!] Error: {e}")
    
    except KeyboardInterrupt:
        print("\n[+] Keyboard interrupt, closing connection...")
        stop_event.set()
    except EOFError:
        print("\n[+] EOF, closing connection...")
        stop_event.set()
    
    finally:
        # Close session
        try:
            requests.post(f"{LOAD_BALANCER}/shell_close", 
                        json={"server": server, "session_id": session_id}, 
                        timeout=10)
        except:
            pass
        
        stop_event.set()
        reader_thread.join(timeout=2)


def menu():
    while True:
        print("\n========== Mini Cloud Client ==========")
        print("1. Create VM")
        print("2. List VMs")
        print("3. SSH (exec) into VM")
        print("4. Delete VM")
        print("5. Exit")
        print("=======================================")
        choice = input("Enter choice: ").strip()
        if choice == "1":
            create_vm()
        elif choice == "2":
            list_vms()
        elif choice == "3":
            ssh_into_vm()
        elif choice == "4":
            delete_vm()
        elif choice == "5":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice.")


if __name__ == "__main__":
    menu()

