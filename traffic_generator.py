import time
import random
import requests
import sys

BASE_URL = "http://localhost:5001"

def generate_traffic():
    print(f"🚀 Starting traffic generator for {BASE_URL}...")
    print("Press Ctrl+C to stop.")
    
    while True:
        try:
            action = random.choice(['read', 'create', 'delete', 'error'])
            
            if action == 'read':
                requests.get(f"{BASE_URL}/tasks")
                print(".", end="", flush=True)       
            elif action == 'create':
                requests.post(f"{BASE_URL}/task", json={"content": f"Auto task {random.randint(1, 1000)}"})
                print("+", end="", flush=True)       
            elif action == 'delete':
                requests.delete(f"{BASE_URL}/task?id=1")
                print("-", end="", flush=True)        
            elif action == 'error':
                requests.get(f"{BASE_URL}/simulate-error")
                print("!", end="", flush=True)
            time.sleep(random.uniform(0.1, 1.0))
        except Exception as e:
            print(f"\nConnection Error: {e}")
            time.sleep(5)
if __name__ == "__main__":
    generate_traffic()