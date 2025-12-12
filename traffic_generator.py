import time
import random
import requests
import sys

# REPLACE THIS WITH YOUR TERRAFORM OUTPUT IP
SERVER_IP = "13.212.81.142" 
BASE_URL = f"http://{SERVER_IP}"

def generate_traffic():
    print(f"🚀 Starting traffic generator for {BASE_URL}...")
    print("Press Ctrl+C to stop.")
    
    while True:
        try:
            # 1. Pick a random action
            action = random.choice(['read', 'create', 'delete', 'error'])
            
            if action == 'read':
                requests.get(f"{BASE_URL}/tasks")
                print(".", end="", flush=True)
                
            elif action == 'create':
                requests.post(f"{BASE_URL}/task", json={"content": f"Auto task {random.randint(1, 1000)}"})
                print("+", end="", flush=True)
                
            elif action == 'delete':
                # Try to delete task ID 1 (might fail if not exists, which is fine)
                requests.delete(f"{BASE_URL}/task?id=1")
                print("-", end="", flush=True)
                
            elif action == 'error':
                # Hit the chaos endpoint
                requests.get(f"{BASE_URL}/simulate-error")
                print("!", end="", flush=True)

            # Sleep randomly between 0.1s and 1s to make the graph look natural
            time.sleep(random.uniform(0.1, 1.0))
            
        except Exception as e:
            print(f"\nConnection Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    generate_traffic()