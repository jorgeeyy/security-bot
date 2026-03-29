import os
from config import settings

def load_whitelist():
    if not os.path.exists(settings.WHITELIST_PATH):
        return set()
    with open(settings.WHITELIST_PATH, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_whitelist(whitelist_set):
    with open(settings.WHITELIST_PATH, "w") as f:
        for ip in whitelist_set:
            f.write(f"{ip}\n")

def add_to_whitelist(ip):
    wl = load_whitelist()
    wl.add(ip)
    save_whitelist(wl)
    return wl

def remove_from_whitelist(ip):
    wl = load_whitelist()
    if ip in wl:
        wl.remove(ip)
    save_whitelist(wl)
    return wl
