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
        match = LogParser.NGINX_PATTERN.match(line.strip())
        if not match:
            return None
        
        groups = match.groups()
        try:
            # Parse [27/Jul/2023:14:52:19 +0000]
            # timestamp format: %d/%b/%Y:%H:%M:%S %z
            # Actually we can just return it or parse to seconds
            # Nginx timestamp: 24/Mar/2026:12:00:00 +0000
            # dt = datetime.strptime(groups[1], "%d/%b/%Y:%H:%M:%S %z")
            # But simpler to just use current time if we're streaming live,
            # though log timestamp is better for precision.
            
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
