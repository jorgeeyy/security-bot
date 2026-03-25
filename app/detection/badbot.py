class BadBotDetector:
    BAD_UA_LIST = [
        "python-requests",
        "curl",
        "wget",
        "postman",
        "nmap",
        "masscan",
        "gobuster",
        "sqlmap"
    ]

    @staticmethod
    def is_bad_bot(user_agent: str):
        if not user_agent or user_agent == "-":
            return True, "Empty User-Agent"
        
        ua_lower = user_agent.lower()
        for bot in BadBotDetector.BAD_UA_LIST:
            if bot in ua_lower:
                return True, f"Blocked User-Agent: {bot}"
        
        return False, None
