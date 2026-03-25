import asyncio
import os
import aiofiles
from app.config import settings

class LogWatcher:
    async def watch(self, file_path, callback, name="LOG"):
        """Asynchronously stream lines from a file, handling rotation etc."""
        print(f"[WATCHER] Starting watcher for {name}: {file_path}")
        
        # If mock mode, start from beginning so we see simulation output
        # For SSH logs, we'll also start from beginning in Mock mode
        seek_pos = os.SEEK_SET if settings.MOCK_MODE else os.SEEK_END

        if not os.path.exists(file_path):
            # Create dummy if not exists for testing
            with open(file_path, "a") as f:
                pass

        async with aiofiles.open(file_path, mode='r') as f:
            # If we're not starting at the beginning, we might miss the first few lines 
            # if we don't seek carefully. SEEK_END is right for production.
            await f.seek(0, seek_pos)
            
            while True:
                line = await f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    
                    # check if file was rotated (e.g. current size < current seek pos)
                    try:
                        current_size = os.path.getsize(file_path)
                        current_pos = await f.tell()
                        if current_size < current_pos:
                            print(f"[WATCHER] {name} Rotated. Reopening...")
                            await f.close()
                            f = await aiofiles.open(file_path, mode='r')
                    except FileNotFoundError:
                        await asyncio.sleep(1)
                        continue
                    
                    continue
                
                # We have a line!
                await callback(line.strip())

    async def watch_all_logs(self, nginx_callback, ssh_callback):
        """Monitor both Nginx and SSH auth logs."""
        tasks = [
            self.watch(settings.NGINX_LOG_PATH, nginx_callback, "NGINX"),
            self.watch(settings.SSH_LOG_PATH, ssh_callback, "SSH")
        ]
        await asyncio.gather(*tasks)
