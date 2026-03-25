import asyncio
import os
import aiofiles
from app.config import settings

class LogWatcher:
    async def watch(self, file_path, callback):
        """Asynchronously stream lines from a file, handling rotation etc."""
        if not os.path.exists(file_path):
            # Create dummy if not exists for testing
            with open(file_path, "a") as f:
                pass

        # If mock mode, start from beginning so we see simulation output
        seek_pos = os.SEEK_SET if settings.MOCK_MODE else os.SEEK_END

        async with aiofiles.open(file_path, mode='r') as f:
            await f.seek(0, seek_pos)
            
            while True:
                line = await f.readline()
                if not line:
                    # Check for rotation: if current pos > file size? Or just wait.
                    # Standard simple tail -f doesn't always handle rotation well.
                    # We can stat the file periodically.
                    await asyncio.sleep(0.1)
                    
                    # check if file was rotated (e.g. current size < current seek pos)
                    try:
                        current_size = os.path.getsize(file_path)
                        current_pos = await f.tell()
                        if current_size < current_pos:
                            # Reopen
                            await f.close()
                            f = await aiofiles.open(file_path, mode='r')
                    except FileNotFoundError:
                        # try reopen
                        await asyncio.sleep(1)
                        continue
                    
                    continue
                
                # We have a line!
                await callback(line.strip())

    async def watch_nginx_logs(self, access_callback, error_callback=None):
        tasks = []
        tasks.append(self.watch(settings.NGINX_LOG_PATH, access_callback))
        # Note: can add error.log path in config and add task here
        await asyncio.gather(*tasks)
