import geopandas as gpd
import matplotlib.pyplot as plt
from PlanesGetter import poland_bbox, BBox

def draw_base_geography(ax, bbox):
    # Countries
    countries = gpd.read_file("naturalearth_lowres")
    
    countries.plot(ax=ax, facecolor="white", edgecolor="black", linewidth=0.8)

    # Rivers (10m scale)
    rivers = gpd.read_file(
        "ne_10m_rivers_lake_centerlines.shp"
    )
    rivers.plot(ax=ax, color="black", linewidth=0.4)

    # Cities (major only)
    cities = gpd.read_file(
        "ne_10m_populated_places.shp"
    )
    major = cities[cities["SCALERANK"] <= 5]  # capitals & large cities
    major.plot(ax=ax, color="black", markersize=8)


def render_geographic_map(bbox, out_path="map.png"):
    fig, ax = plt.subplots(figsize=(10, 8))

    draw_base_geography(ax, bbox)

    ax.set_xlim(bbox.min_lon, bbox.max_lon)
    ax.set_ylim(bbox.min_lat, bbox.max_lat)
    ax.set_axis_off()

    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


render_geographic_map(poland_bbox)

