from logging.handlers import RotatingFileHandler
import time
import logging
from DataFetch import DataFetch, poland_bbox
from ScreenRender import ScreenRender
from ScreenDriver import get_screen_driver

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
handler = RotatingFileHandler("./app_log.log", maxBytes=5 * 1024 * 1024, backupCount=3)
log.addHandler(handler)


def main():
    log.info("Starting Weather Station application...")

    try:
        dtf = DataFetch()
        scrr = ScreenRender()
        screen = get_screen_driver()
        log.info("Initialization successful.")
    except Exception as e:
        log.critical(f"Failed to initialize components: {e}", exc_info=True)
        return

    while True:
        try:
            log.info("Fetching new weather data...")
            data = dtf()

            log.info("Rendering screen layout...")
            img = scrr(data)

            log.info("Updating E-Ink display...")
            screen.update(img)

            log.info("Update complete. Sleeping for 60 seconds.")
            time.sleep(900)

        except KeyboardInterrupt:
            log.warning("Application stopped by user (Ctrl+C).")
            break


if __name__ == "__main__":
    import time
    while True:
        main()  # your existing function
        time.sleep(60)  # sleep between iterations
