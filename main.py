import time
from PlanesGetter import PlanesGetter, poland_bbox
from Rendering import ImageRendering

def lonlat_to_pixel(position, bbox, img_shape):
    lon, lat = position
    img_h, img_w = img_shape

    u = (lon - bbox.min_lon) / (bbox.max_lon - bbox.min_lon)
    v = (lat - bbox.min_lat) / (bbox.max_lat - bbox.min_lat)

    bbox_ar = (bbox.max_lon - bbox.min_lon) / (bbox.max_lat - bbox.min_lat)
    img_ar = img_w / img_h

    if img_ar > bbox_ar:
        draw_w = bbox_ar * img_h
        pad_x = (img_w - draw_w) / 2
        pad_y = 0
        w = draw_w
        h = img_h
    else:
        draw_h = img_w / bbox_ar
        pad_x = 0
        pad_y = (img_h - draw_h) / 2
        w = img_w
        h = draw_h

    x = pad_x + u * w
    y = pad_y + (1 - v) * h

    return x, y

def main():
    img_shape = (880, 576)
    plg = PlanesGetter()
    imr = ImageRendering(img_shape)

    while(True):
        planes = plg.get_all_planes()
        pol_planes = plg.filter_by_geo(planes, poland_bbox)
        plane_list = plg.get_basic(pol_planes)

        plane_draw = [lonlat_to_pixel(plane, poland_bbox, img_shape) for plane in plane_list]
        imr.render_basic(plane_draw)
        imr.show_image()
        time.sleep(5)


if __name__ == "__main__":
    main()
