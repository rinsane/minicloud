#!/usr/bin/env python3
"""
Test script to verify interactive SSH functionality
Run this while the servers are running to test the endpoints
"""

import requests
import time
import json

LOAD_BALANCER = "http://127.0.0.1:8000"

def test_create_vm():
    print("\n[TEST] Creating a test VM...")
    res = requests.post(f"{LOAD_BALANCER}/create_vm", 
                       json={"name": "test-vm-interactive"}, 
                       timeout=30)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    return res.status_code == 201

def test_list_vms():
    print("\n[TEST] Listing all VMs...")
    res = requests.get(f"{LOAD_BALANCER}/list_all", timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    return res.status_code == 200

def test_shell_session():
    print("\n[TEST] Starting interactive shell session...")
    res = requests.post(f"{LOAD_BALANCER}/shell_session",
                       json={"server": "http://127.0.0.1:5000", "name": "test-vm-interactive"},
                       timeout=30)
    print(f"Status: {res.status_code}")
    data = res.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if res.status_code != 201:
        return None
    
    session_id = data.get("session_id")
    return session_id

def test_shell_input(session_id, command):
    print(f"\n[TEST] Sending command: {command}")
    res = requests.post(f"{LOAD_BALANCER}/shell_input",
                       json={
                           "server": "http://127.0.0.1:5000",
                           "session_id": session_id,
                           "input": command
                       },
                       timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    return res.status_code == 200

def test_shell_output(session_id):
    print(f"\n[TEST] Reading shell output...")
    res = requests.post(f"{LOAD_BALANCER}/shell_output",
                       json={
                           "server": "http://127.0.0.1:5000",
                           "session_id": session_id
                       },
                       timeout=5)
    print(f"Status: {res.status_code}")
    print(f"Output:\n{res.text}")
    return res.status_code == 200

def test_shell_close(session_id):
    print(f"\n[TEST] Closing shell session...")
    res = requests.post(f"{LOAD_BALANCER}/shell_close",
                       json={
                           "server": "http://127.0.0.1:5000",
                           "session_id": session_id
                       },
                       timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    return res.status_code == 200

def test_delete_vm():
    print("\n[TEST] Deleting test VM...")
    res = requests.post(f"{LOAD_BALANCER}/delete_vm",
                       json={
                           "server": "http://127.0.0.1:5000",
                           "name": "test-vm-interactive"
                       },
                       timeout=30)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    return res.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("Interactive SSH Shell Endpoints - Test Suite")
    print("=" * 60)
    
    try:
        # Test VM creation
        if not test_create_vm():
            print("❌ VM creation failed!")
            exit(1)
        
        time.sleep(2)
        
        # Test listing
        if not test_list_vms():
            print("❌ VM listing failed!")
            exit(1)
        
        time.sleep(1)
        
        # Test shell session creation
        session_id = test_shell_session()
        if not session_id:
            print("❌ Shell session creation failed!")
            exit(1)
        
        time.sleep(1)
        
        # Test sending commands
        commands = [
            "pwd",
            "ls -la",
            "echo 'Hello from interactive shell!'",
            "uname -a",
            "date"
        ]
        
        for cmd in commands:
            if not test_shell_input(session_id, cmd):
                print(f"❌ Failed to send command: {cmd}")
                break
            
            time.sleep(0.5)
            
            if not test_shell_output(session_id):
                print(f"❌ Failed to read output after: {cmd}")
                break
            
            time.sleep(0.5)
        
        # Close session
        if not test_shell_close(session_id):
            print("❌ Shell session closure failed!")
            exit(1)
        
        time.sleep(1)
        
        # Delete VM
        if not test_delete_vm():
            print("❌ VM deletion failed!")
            exit(1)
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Interactive SSH is working!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        exit(1)
