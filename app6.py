from flask import Flask, send_file, render_template
import io
import scipy.interpolate
import requests
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import matplotlib.patches as patches
import matplotlib.image as mpimg
import matplotlib.colors as mcolors
from concurrent.futures import ThreadPoolExecutor
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from scipy.interpolate import griddata  # For interpolation
from datetime import datetime
import pytz

app6 = Flask(__name__)

# Your API key for the weather data
API_KEY = '6e1f7ca9bda347cdb5a5b9259a0bafc9'

# Define locations (simplified for example)
locations = {
    "Chicago": {"lat": 41.8781, "lon": -87.6298},
    "Oak Park": {"lat": 41.8807, "lon": -87.7840},
    "Cicero": {"lat": 41.8369, "lon": -87.7461},
    "La Grange": {"lat": 41.8190, "lon": -87.8680},
    "Elmhurst": {"lat": 41.8990, "lon": -87.9403},
    "Oak Brook": {"lat": 41.8506, "lon": -87.9515},
    "Skokie": {"lat": 42.0334, "lon": -87.7420},
    "Downers Grove": {"lat": 41.8080, "lon": -88.0113},
    "Des Plaines": {"lat": 42.0334, "lon": -87.8830},
    "Arlington Heights": {"lat": 42.0394, "lon": -87.9606},
    "Park Ridge": {"lat": 42.0116, "lon": -87.8237},
    "Elmwood Park": {"lat": 41.9239, "lon": -87.7839},
    "Schaumburg": {"lat": 42.0334, "lon": -88.0534},
    "O'Hare Airport": {"lat": 41.978611, "lon": -87.904724},
    "Midway Airport": {"lat": 41.78, "lon": -87.76},
    "Addison": {"lat": 41.9295, "lon": -88.0037},
    "Lombard": {"lat": 41.8850, "lon": -88.0086},
    "Franklin Park": {"lat": 41.9296, "lon": -87.8697},
    "Lincoln Park": {"lat": 41.9216, "lon": -87.6455},
    "Bridgeport": {"lat": 41.8319, "lon": -87.6643},
    "Oak Lawn": {"lat": 41.7161, "lon": -87.7467},
    "Dalton": {"lat": 41.6199, "lon": -87.6226},
    "Roseland": {"lat": 41.7010, "lon": -87.6087},
    "Darien": {"lat": 41.7463, "lon": -87.9965},
    "Burr Ridge": {"lat": 41.7520, "lon": -87.9401},
    "Willow Springs": {"lat": 41.7100, "lon": -87.8645},
    "Orland Park": {"lat": 41.6300, "lon": -87.8539},
    "Palos Hills": {"lat": 41.68, "lon": -87.81},
    "Blue Island": {"lat": 41.6569, "lon": -87.6847},
    "South Shore": {"lat": 41.7591, "lon": -87.5853},
    "Uptown": {"lat": 41.9747, "lon": -87.6547},
    "Albany Park": {"lat": 41.9760, "lon": -87.7250},
    "Englewood": {"lat": 41.7795, "lon": -87.6737},
    "Lemont": {"lat": 41.6689, "lon": -87.9405},
    "Homer Glen": {"lat": 41.6302, "lon": -87.9282},
    "interpol": {"lat": 41.79535, "lon": -87.80705},
    "interpol2": {"lat": 41.81, "lon": -87.798},
    "North": {"lat": 42.06, "lon": -87.8},
    "North1": {"lat": 42.06, "lon": -87.7},
    "North2": {"lat": 42.06, "lon": -87.6},
    "North3": {"lat": 42.06, "lon": -87.5},
    "North4": {"lat": 42.06, "lon": -87.9},
    "North5": {"lat": 42.06, "lon": -88.0},
    "North6": {"lat": 42.06, "lon": -88.1},
    "South": {"lat": 41.58, "lon": -87.8},
    "South1": {"lat": 41.58, "lon": -87.7},
    "South3": {"lat": 41.58, "lon": -87.5},
    "South4": {"lat": 41.58, "lon": -87.9},
    "South5": {"lat": 41.58, "lon": -88.0},
    "South6": {"lat": 41.58, "lon": -88.1},
    "East": {"lat": 41.82, "lon": -87.5},
    "East1": {"lat": 41.92, "lon": -87.5},
    "East2": {"lat": 42.02, "lon": -87.5},
    "East3": {"lat": 42.12, "lon": -87.5},
    "East4": {"lat": 41.72, "lon": -87.5},
    "East5": {"lat": 41.62, "lon": -87.5},
    "East6": {"lat": 41.52, "lon": -87.5},
    "West": {"lat": 41.82, "lon": -88.1},
    "West1": {"lat": 41.92, "lon": -88.1},
    "West2": {"lat": 42.02, "lon": -88.1},
    "West3": {"lat": 42.12, "lon": -88.1},
    "West4": {"lat": 41.72, "lon": -88.1},
    "West5": {"lat": 41.62, "lon": -88.1},
    "West6": {"lat": 41.52, "lon": -88.1},
    # Add more locations...
}

@app6.route('/')

@app6.route('/weather-map')
def map6_view():
    # Step 1: Concurrently fetch weather data for all locations
    with ThreadPoolExecutor() as executor:
        weather_data_list = list(executor.map(fetch_weather_data, locations.keys(), locations.values()))

    # Filter out any None responses (if some data was not fetched)
    weather_data_list = [data for data in weather_data_list if data]

    # Extract latitudes, longitudes, and cloud cover values
    lats = []
    lons = []
    aqis = []

    for data in weather_data_list:
        city_name = data['city_name']
        aqi = data['aqi']  # Cloud cover percentage
        coords = locations[city_name]
        lats.append(coords['lat'])
        lons.append(coords['lon'])
        aqis.append(aqi)

    # Step 2: Create the map and plot the data
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([-88.08, -87.54, 41.58, 42.06])

    # Your map background image
    R = mpimg.imread("525map.jpeg")
    ax.imshow(R, origin='upper', extent=[-88.08, -87.52, 41.58, 42.06], transform=ccrs.PlateCarree(), zorder=1)

    # Add map features
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.RIVERS, linestyle='-')
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # Step 3: Create a grid for cloud cover (interpolation)
    lat_grid = np.linspace(41.58, 42.06, 100)  # Adjust grid range as per your data
    lon_grid = np.linspace(-88.08, -87.54, 100)
    lon, lat = np.meshgrid(lon_grid, lat_grid)


    # Interpolate the cloud cover data onto the grid (using scipy's griddata)
    grid_aqi = griddata((lons, lats), aqis, (lon, lat), method='cubic')
    # Plot the contour map with color fill
    aqi_boundaries = [0, 50, 100, 150, 200, 300, 400]  # Add one more boundary at 12
    aqi_labels = ["Good", "Moderate", "Unhealthy for Sensitive Groups", "Unhealthy", "Very Unhealthy", "Hazardous", ""]  # Updated label for higher aqi index
    # Define the corresponding colors for each aqi range
    colors = [
        '#00FF00',  # Green for "Low"
        '#FFFF00',  # Yellow for "Moderate"
        '#FF8000',  # Orange for "High"
        'red',  # Purple for "Very High"
        'purple',  # Light Blue for "Extreme"
        'brown',   # Blue for "Extreme+"
        'brown'   # Blue for "Extreme+"(can represent higher aqi values)
    ]

    # Create a linear segmented colormap with the gray shades
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(aqi_boundaries, cmap.N)
    contour = ax.contourf(lon_grid, lat_grid, grid_aqi, levels= aqi_boundaries, cmap=cmap, norm=norm, alpha= 0.6, transform=ccrs.PlateCarree())


    # Add colorbar for cloud cover
    cbar = fig.colorbar(contour, ax=ax, orientation="vertical", shrink=0.5, label="Air Quality Index")
    cbar.set_ticks(aqi_boundaries)  # Set ticks at the boundaries
    cbar.set_ticklabels(aqi_labels)  # Set custom labels for the ticks

    # Step 5: Plot data for each location (cities)
    for city, coords in locations.items():
        LAT, LON = coords["lat"], coords["lon"]
        weather_data = next((data for data in weather_data_list if data['city_name'] == city), None)
        uv = weather_data['aqi']

        if city == "Chicago":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))

        if city == "Oak Park":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Cicero":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "La Grange":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Elmhurst":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Oak Brook":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Skokie":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Downers Grove":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Des Plaines":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON + 0.02, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Arlington Heights":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Park Ridge":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Elmwood Park":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Schaumburg":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Addison":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Lombard":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "O'Hare Airport":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Midway Airport":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Franklin Park":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Lincoln Park":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Bridgeport":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Oak Lawn":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Roseland":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Dalton":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Darien":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Burr Ridge":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Willow Springs":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Orland Park":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Palos Hills":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Blue Island":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "South Shore":
            ax.text(LON - 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Uptown":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Albany Park":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Englewood":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Lemont":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
        if city == "Homer Glen":
            ax.text(LON + 0.005, LAT + 0.0, f"{city}",
                    fontsize=8, color='white', zorder=1.8, transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
            ax.text(LON, LAT + 0.01, f"{uv}", color='white', fontweight='bold', ha='center', fontsize=10,
                transform=ccrs.PlateCarree(), bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))




    # Get the current UTC time
    current_time = datetime.utcnow()

    # Convert to Central Time (CDT or CST depending on daylight saving)
    central_tz = pytz.timezone('America/Chicago')
    central_time = pytz.utc.localize(current_time).astimezone(central_tz)

    # Format the time to be in the desired format 'MM/DD/YYYY at HH:MM AM/PM CDT'
    formatted_time = central_time.strftime("%m/%d/%Y at %I:%M %p CDT")

    # Set the title with the date and time in Central Time
    ax.set_title(f"Air Quality Observations as of {formatted_time}")

    # Step 6: Generate and return the image as a response
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)  # Rewind to the start of the BytesIO object
    return send_file(img, mimetype='image/png')

def fetch_weather_data(city, coords):
    """Fetch weather data from the API."""
    lat, lon = coords["lat"], coords["lon"]
    url = f'https://api.weatherbit.io/v2.0/current?lat={lat}&lon={lon}&key={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather_data = data['data'][0]
        weather_data['city_name'] = city  # Add city name to the weather data for easy reference
        return weather_data
    return None

if __name__ == '__main__':
    app6.run(debug=True)