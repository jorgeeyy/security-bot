import asyncio
import os
import aiofiles
from app.config import settings

class LogWatcher:
    async def watch(self, file_path, callback, name="LOG"):
        """Asynchronously stream lines from a file, handling rotation etc."""
        print(f"[WATCHER] Starting watcher for {name}: {file_path}")
        
        seek_pos = os.SEEK_SET if settings.MOCK_MODE else os.SEEK_END

        if not os.path.exists(file_path):
            # Create dummy if not exists for testing
            with open(file_path, "a") as f:
                pass

        while True:
            async with aiofiles.open(file_path, mode='r') as f:
                await f.seek(0, seek_pos)
                
                rotated = False
                while not rotated:
                    line = await f.readline()
                    if not line:
                        await asyncio.sleep(0.1)
                        # check if file was rotated
                        try:
                            current_size = os.path.getsize(file_path)
                            current_pos = await f.tell()
                            if current_size < current_pos:
                                print(f"[WATCHER] {name} Rotated. Reopening...")
                                rotated = True
                        except FileNotFoundError:
                            pass
                    else:
                        await callback(line.strip())
            
            # Subsequence rotations should read from the beginning of the new file
            seek_pos = os.SEEK_SET

    async def watch_all_logs(self, nginx_callback, ssh_callback):
        """Monitor both Nginx and SSH auth logs."""
        tasks = [
            self.watch(settings.NGINX_LOG_PATH, nginx_callback, "NGINX"),
            self.watch(settings.SSH_LOG_PATH, ssh_callback, "SSH")
        ]
        await asyncio.gather(*tasks)
