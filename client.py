"""
Pure HTTP client for the mini cloud.
No direct Docker access — all operations go through the load balancer.
"""

import requests
import sys

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
    print(f"\n[+] Connecting to {name} on {server}...\n")
    res = requests.post(f"{LOAD_BALANCER}/exec_vm", json={"server": server, "name": name, "cmd": "echo 'Connected to VM:' && uname -a"}, timeout=30)
    print(res.text)


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

