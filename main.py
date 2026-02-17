from logging.handlers import RotatingFileHandler
import time
import logging
from DataFetch import DataFetch, poland_bbox
from ScreenRender import ScreenRender
from ScreenDriver import get_screen_driver
import asyncio

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = RotatingFileHandler("./app_log.log", maxBytes=5 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s'
)
handler.setFormatter(formatter)
log.addHandler(handler)

UPDATE_PERIOD_S = 5 # 15 minutes in seconds

async def weather_producer(queue):
    dtf = DataFetch()
    while True:
        try:
            log.debug("Producer: Fetching new weather data...")
            data = await dtf() # If this is a network call, ideally it should be awaited
            
            # Put data in queue. If queue is full, this waits.
            await queue.put(data)
            log.debug(f"Producer: Data sent to queue. Sleeping {UPDATE_PERIOD_S//60}m.")
            
            await asyncio.sleep(UPDATE_PERIOD_S) 
        except Exception as e:
            log.error(f"Producer Error: {e}")
            await asyncio.sleep(60)

async def weather_display(queue):
    """Task 2: Waits for data from the queue and updates the screen."""
    scrr = ScreenRender()
    screen = get_screen_driver()
    
    while True:
        # This line "pauses" the coroutine until there is something in the queue
        data = await queue.get()
        
        try:
            log.debug("Consumer: Data received. Rendering...")
            img = scrr(data)
            log.debug("Image generated. Updating display...")
            screen.update(img)
            log.debug("Consumer: Display updated.")
        except Exception as e:
            log.error(f"Consumer Error: {e.__class__.__name__}")
        finally:
            # Tell the queue the task is done
            queue.task_done()

async def main():
    # Create a queue with a max size of 1 to avoid "backlogging" old weather data
    queue = asyncio.Queue(maxsize=1)

    log.info("Starting Weather Station...")

    # Run both tasks concurrently
    await asyncio.gather(
        weather_producer(queue),
        weather_display(queue)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.warning("Application stopped by user.")
