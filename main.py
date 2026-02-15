import time
from DataFetch import DataFetch, poland_bbox
from ScreenRender import ScreenRender
from ScreenDriver import get_screen_driver
def main():
    dtf = DataFetch()
    scrr = ScreenRender()
    screen = get_screen_driver()

    while(True):
        data = dtf()
        img = scrr(data)
        screen.update(img)
        time.sleep(5)

if __name__ == "__main__":
    main()
