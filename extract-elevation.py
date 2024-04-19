import argparse
import numpy as np
import gzip
import shutil
import zipfile
import os
import locale
import json
from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress
from rich.prompt import Prompt
from countries_data import COUNTRIES_DATA
import requests
from dotenv import load_dotenv
import tempfile
from http import cookiejar
from urllib import request
from urllib.parse import urlencode
from osgeo import gdal

load_dotenv()


# Set the locale to the default system locale
locale.setlocale(locale.LC_ALL, '')

# read NASA bearer from environment variables
NASA_BEARER = os.getenv("NASA_BEARER")



custom_theme = Theme({
    'info': 'green',
    'warning': 'yellow',
    'error': 'bold red',
    'progress': 'blue'
})

# Create a console object with the custom theme
console = Console(theme=custom_theme)

# Define the base URL for the NASADEM dataset with the elevation data
NASA_URL = "https://e4ftl01.cr.usgs.gov/MEASURES/NASADEM_SHHP.001/2000.02.11/"

# Function to log an info message
def log(message, verbose):
    if verbose:
        console.print(f"[info]INFO:[/info] {message}")

# Function to log an error message and exit the program
def error(message):
    console.print(f"[error]ERROR:[/error] {message}")
    exit(1)

# Function to ask the user if they want to extract data for the whole Spain or for specific regions
def process_spain_regions():
    choice = Prompt.ask(
        "Do you want to extract data for the whole Spain or for specific regions?",
        choices=["1", "2"],
        default="1",
        show_choices=True,
        show_default=True,
    )
    if choice == "1":
        return COUNTRIES_DATA["ESP"]
    elif choice == "2":
        console.print("Select the region you want to extract data for:")
        console.print("1. Canary Islands")
        console.print("2. Balearic Islands")
        console.print("3. Spanish Peninsula")
        region_choice = Prompt.ask(
            "Enter your choice (1/2/3): ",
            choices=["1", "2", "3"],
            default="3",
            show_choices=True,
            show_default=True,
        )
        if region_choice == "1":
            return COUNTRIES_DATA["ESP_CANARY"]
        elif region_choice == "2":
            return COUNTRIES_DATA["ESP_BALEARIC"]
        elif region_choice == "3":
            return COUNTRIES_DATA["ESP_PENINSULA"]
        else:
            console.print("[bold red]Error: Invalid region choice.[/bold red]")
            return None
    else:
        console.print("[bold red]Error: Invalid choice.[/bold red]")
        return None

# Function to download a file from a URL and save it to a local path
# It uses NASA_BEARER to authenticate the request
def download_url(url, save_path, verbose):
    headers = {"Authorization": f"Bearer {NASA_BEARER}"}
    try:
        r = requests.get(url, stream=True, allow_redirects=True, headers=headers)
        r.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=8192):
                fd.write(chunk)
        return True  # Return True to indicate successful download
    except requests.exceptions.RequestException as e:
        log(f"Error downloading {url}: {e} skipping...",verbose)
        return True  # Return True to indicate failed download but

# Function to unzip a file and extract the .hgts files
def unzip_file(zip_file, verbose):
    extracted_hgts = []
    
    if not os.path.exists(zip_file):
        return extracted_hgts
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        listOfFileNames = zip_ref.namelist()
        for fileName in listOfFileNames:
            log(f"Unziping´{zip_file}", verbose)
            if fileName.endswith('.hgts'):
                zip_ref.extract(fileName, os.path.dirname(zip_file))
                log(f"Extracted {fileName} from {zip_file}", verbose)
                extracted_hgts.append(os.path.join(os.path.dirname(zip_file), fileName))
                break

            else:
                pass
    return extracted_hgts

# Function to obtain the elevation data from the .hgts files
def obtain_elevation(hgts_files, verbose):
    total_lon, total_lat, total_elevations = [], [], []
    for hgts_file in hgts_files:
        file = hgts_file[0]
        
        # Extract latitude and longitude from the filename
        lat = int(file[-11:-9])
        lon = int(file[-8:-5])
        if file[-12] == 's':
            lat = -lat
        if file[-9] == 'w':
            lon = -lon
        
        raster = gdal.Open(file)
        elevations = raster.ReadAsArray()
        elevations[elevations == -32768] = np.nan
        
        # Generate latitude and longitude values for this specific file
        lat_vals = np.arange(lat + 1, lat, -0.00277777777777)
        lon_vals = np.arange(lon, lon + 1, 0.00277777777777)
        lats, lons = np.meshgrid(lat_vals, lon_vals)
        
        total_lat.append(lats)
        total_lon.append(lons)
        total_elevations.append(elevations)

    log(f"Extracted elevation data from {len(hgts_files)} files", verbose)
    return total_lat, total_lon, total_elevations

def extract_elevation(min_lat, max_lat, min_lon, max_lon, verbose):
    
    
    #create a temp dir from the program path
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)

    hgts_files = []
    # The NASADEM dataset is stored in 1-degree tiles, so we need to download multiple tiles to cover the bounding box
    # The filename format is NASADEM_SHHP_{n or s}{latitude 2 digits zero padded}{e or w}{longitude 2 digits zero padded}.zip
    # https://e4ftl01.cr.usgs.gov/MEASURES/NASADEM_SHHP.001/2000.02.11/NASADEM_SHHP_n42e000.zip
    for lat in range(int(min_lat), int(max_lat)):
        for lon in range(int(min_lon), int(max_lon)):
            # Define the latitude and longitude values for the tile
            lat_str = f"{abs(lat):02d}"
            lon_str = f"{abs(lon):03d}"
            lat_dir = "n" if lat >= 0 else "s"
            lon_dir = "e" if lon >= 0 else "w"

            # Define the filename for the tile
            filename = f"NASADEM_SHHP_{lat_dir}{lat_str}{lon_dir}{lon_str}.zip"

            # Define the URL to download the tile
            url = f"{NASA_URL}{filename}"

            #define the path to save the file
            save_path = os.path.join(temp_dir, filename)

            # Download the tile from the NASADEM dataset
            # If the file does not exist, skip to the next tile
            if not os.path.exists(save_path):
                log(f"Downloading tile {filename} from {url}", verbose)
                try:
                    download_url(url, save_path, verbose)
                    log(f"Downloaded tile {filename}", verbose)
                except Exception as e:
                    error(f"Error downloading tile {filename}: {e}")
            else:
                log(f"Tile {filename} already exists, skipping download", verbose)

            #From the zip we extract the .hgt file
            extracted_hgts = unzip_file(save_path, verbose)
            if extracted_hgts:
                hgts_files.append(extracted_hgts)
            else:
                log(f"No .hgts files found in {save_path}, skipping...", verbose)
                continue

            # If the tile is downloaded, extract the elevation data from the tile

    return obtain_elevation(hgts_files, verbose)

# Function to export the extracted data to a GeoJSON file
def export_geojson(outputfile, global_lat, global_lon, global_elevations, verbose):
    features = []
    for lats, lons, elevations in zip(global_lat, global_lon, global_elevations):
        for row in range(lats.shape[0]):  # use shape instead of len
            for col in range(lats.shape[1]):
                lat = lats[row][col]
                lon = lons[row][col]
                alt = elevations[row][col]

                # Skip points with no elevation data
                if np.isnan(alt):
                    continue

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(lon), float(lat), float(alt)]
                    }
                }
                features.append(feature)

    # Build final GeoJSON FeatureCollection
    geojson = {"type": "FeatureCollection", "features": features}

    log(f"Generated {len(features)} coordinates", verbose)

    with open(f"{outputfile}.json", "w") as f:
        json.dump(geojson, f)

    log(f"Extracted data written to {outputfile}.json", verbose)




# Function to export the extracted data to a CSV file
def export_csv(outputfile, global_lat, global_lon, global_elevations, verbose):
    with open(outputfile, 'w') as f:
        f.write("latitude,longitude,elevation\n")
        for row in range(len(elevations)):
            for col in range(len(elevations[0])):
                lat = lats[row][col]
                lon = lons[row][col] 
                alt = elevations[row][col]
                
                # Skip points with no elevation data
                if np.isnan(alt):
                    continue
                
                f.write(f"{lat},{lon},{alt}\n")
        
    log(f"[info]Extracted data written to {args.output}.csv[/info]", verbose)

def main():

    global_lat, global_lon, global_elevations = [], [], []

    parser = argparse.ArgumentParser(description='Extract elevation data from given coordinates')
    parser.add_argument('--output', type=str, help='The output filename to write the extracted data to', default='elevation');
    parser.add_argument('--format', type=str, choices=['json', 'csv'], default='json', help='The format to write the extracted data in (default: json)')
    parser.add_argument('--minlat', type=float, help='Minimum latitude of the bounding box')
    parser.add_argument('--maxlat', type=float, help='Maximum latitude of the bounding box')
    parser.add_argument('--minlon', type=float, help='Minimum longitude of the bounding box')
    parser.add_argument('--maxlon', type=float, help='Maximum longitude of the bounding box')
    parser.add_argument('--country', help='ISO3 code of the country to extract data for')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--gzip', action="store_true",  help='Compress the output file with gzip')
    group.add_argument('--zip' , action='store_true', help='Compress the output file with zip')

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('--verbose', action='store_true', help='Print verbose output')
    group2.add_argument('--quiet', action='store_true', help='Suppress all output')

    args = parser.parse_args()

    # if not verbose or quiet set verbose
    if not args.verbose and not args.quiet:
        args.verbose = True
   
    # Check if the output file already exists
    if args.output and os.path.exists(f"{args.output}´.{args.format}"):
        # Ask the user if they want to overwrite the existing file
        response = Prompt.ask(f'The file "{args.output}" already exists. Do you want to overwrite it? (yes/no)', choices=['yes', 'no'])
        if response == 'no':
            return
    if args.country:
            country_data = COUNTRIES_DATA.get(args.country)

            #If args.country is not found in the dictionary, return an error
            if not country_data:
                error("Error: Could not find the country data.")
                return
            # If args.country is ESP we ask to the user if they want to extract data for the whole Spain or for specific regions
            if args.country == "ESP" and args.verbose:
                country_data = process_spain_regions()

                if not country_data:
                    return

            if country_data:
                min_lat = country_data["lat_min"]
                max_lat = country_data["lat_max"]
                min_lon = country_data["lon_min"]
                max_lon = country_data["lon_max"]
                log(f"Extracting data for {country_data['Name']} with bounding box: {min_lat} - {max_lat} (lat), {min_lon} - {max_lon} (lon)", args.verbose)

            else:
                error("Could not find the country data.")
                return
    else:
        # Define the bounding box from the arguments
        min_lat, max_lat,min_lon, max_lon = args.minlat, args.maxlat, args.minlon, args.maxlon

        # if some of the bounding box values are not provided, use the values from the countries_data.py file
        if not min_lat or not max_lat or not min_lon or not max_lon:
            error("Bounding box values not provided. Did you forget to provide the --country argument?")
            return

    # Extract the elevation data from the input file
    global_lat, global_lon, global_elevations = extract_elevation(min_lat, max_lat, min_lon, max_lon, args.verbose)

    # Export the extracted data to the output file
    if args.output:
        if args.format == "json":
            export_geojson(args.output, global_lat, global_lon, global_elevations, args.verbose)
        elif args.format == "csv":
            export_csv(args.output, global_lat, global_lon, global_elevations,args.verbose)


if __name__ == '__main__':
    main()