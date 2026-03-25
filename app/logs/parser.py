import re
from datetime import datetime

class LogParser:
    # Default Nginx format
    # $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
    NGINX_PATTERN = re.compile(
        r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (.*?) (\S+)" (\d+) (\d+) "([^"]*)" "([^"]*)"$'
    )

    @staticmethod
    def parse_line(line: str):
        """Parse Nginx access log lines."""
        match = LogParser.NGINX_PATTERN.match(line.strip())
        if not match:
            return None
        
        groups = match.groups()
        try:
            return {
                "ip": groups[0],
                "time_local": groups[1],
                "method": groups[2],
                "path": groups[3],
                "http_version": groups[4],
                "status": int(groups[5]),
                "bytes_sent": int(groups[6]),
                "referer": groups[7],
                "user_agent": groups[8]
            }
        except Exception:
            return None

    @staticmethod
    def parse_ssh_line(line: str):
        """Parse SSH auth log lines for failed login attempts."""
        # Pattern: Failed password for <user> from <ip> port <port> ssh2
        # Or: Failed password for invalid user <user> from <ip> port <port> ssh2
        pattern = re.compile(r'Failed password for (?:invalid user )?(\S+) from (\S+) port \d+ ssh2')
        match = pattern.search(line)
        if match:
            return {
                "user": match.group(1),
                "ip": match.group(2),
                "type": "SSH_FAILED_LOGIN"
            }
        return None
