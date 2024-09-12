import asyncio
import time

async def sleeping(seconds: int = int()):    
    if seconds > 0:
        
        asyncio.sleep(seconds)
        print('sleeping')
        
async def test():
    await asyncio.gather(sleeping(1), sleeping(2), sleeping(3))
    
asyncio.run(test())