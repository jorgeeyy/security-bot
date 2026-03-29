import asyncio

DEFAULT_JAIL = "sshd"

async def ban_ip(ip: str, jail: str = "nginx-botsearch"):
    await _run("set", jail, "banip", ip)

async def unban_ip(ip: str, jail: str = "nginx-botsearch"):
    # Since we can't be perfectly certain which jail holds them, this unlocks them from default 
    await _run("set", jail, "unbanip", ip)

async def add_ignoreip(ip: str, jail: str = DEFAULT_JAIL):
    await _run("set", jail, "addignoreip", ip)

async def get_banned(jail: str = "nginx-botsearch") -> str:
    return await _run("get", jail, "banned")

async def get_status(jail: str = "nginx-botsearch") -> str:
    return await _run("status", jail)

async def _run(*args) -> str:
    proc = await asyncio.create_subprocess_exec(
        "sudo", "fail2ban-client", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode())
    return stdout.decode()
