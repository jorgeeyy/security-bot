import time
import os
import random

# Default path for testing (relative)
LOG_FILE = "./test_access.log"

# Sample Nginx line format: 
# 127.0.0.1 - - [24/Mar/2026:12:00:00 +0000] "GET /index.html HTTP/1.1" 200 612 "-" "Mozilla/5.0"

def generate_log_line(ip, path, ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"):
    timestamp = time.strftime("%d/%b/%Y:%H:%M:%S +0000")
    return f'{ip} - - [{timestamp}] "GET {path} HTTP/1.1" 200 123 "-" "{ua}"\n'

def append_to_log(line):
    with open(LOG_FILE, "a") as f:
        f.write(line)
        f.flush()

def main():
    print(f"[*] Starting attack simulation against {LOG_FILE}...")
    # Clear the file instead of removing it to avoid Windows Permission Errors
    with open(LOG_FILE, "w") as f:
        f.write("")
    
    # 1. Normal traffic
    print("[+] Simulating normal traffic...")
    for _ in range(3):
        append_to_log(generate_log_line("127.0.0.1", "/"))
        time.sleep(1)

    # 2. Bad Bot Attack
    print("[+] Simulating Bad Bot (sqlmap)...")
    append_to_log(generate_log_line("1.2.3.4", "/", "sqlmap/1.4"))
    
    # 3. Scraper Attack
    print("[+] Simulating Scraper (.env access)...")
    append_to_log(generate_log_line("5.6.7.8", "/.env"))

    # 4. Rate Limit Attack
    print("[+] Simulating Rate Limit burst (30 reqs in 2s)...")
    for _ in range(30):
        append_to_log(generate_log_line("9.10.11.12", "/api/data"))
        time.sleep(0.05)

    # 5. Botnet Activity
    print("[+] Simulating Botnet activity (15 unique IPs in subnet 43.173.1.*)...")
    for i in range(1, 16):
        append_to_log(generate_log_line(f"43.173.1.{i}", "/"))
        time.sleep(0.1)

    print("[*] Simulation complete. Logs generated in", LOG_FILE)

if __name__ == "__main__":
    main()
