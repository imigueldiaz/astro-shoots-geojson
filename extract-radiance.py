import argparse
from osgeo import gdal
import numpy as np
import gzip
import shutil
import zipfile
from countries_data import COUNTRIES_DATA
from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress
import os
import locale
import json

# Set the locale to the default system locale
locale.setlocale(locale.LC_ALL, '')

# Define a custom theme for the console
custom_theme = Theme({
    'info': 'green',
    'warning': 'yellow',
    'error': 'bold red',
    'progress': 'blue'
})

# Create a console object with the custom theme
console = Console(theme=custom_theme)

# Function to convert radiance to Bortle scale with 0.1 precision
def mpsasToBortle(mpsas):
    mpsas_ranges = [21.89, 21.69, 21.25, 20.49, 19.50, 18.94, 18.38, 17.80]
    bortle_values =  range(1, 10)

    if mpsas > mpsas_ranges[0]:
        return 1.0
    elif mpsas <= mpsas_ranges[-1]:
        return 9.0

    for i in range(len(mpsas_ranges) - 1):
        if mpsas_ranges[i + 1] < mpsas <= mpsas_ranges[i]:
            bortle_low = bortle_values[i]
            bortle_high = bortle_values[i + 1]
            mpsas_low = mpsas_ranges[i]
            mpsas_high = mpsas_ranges[i + 1]

            bortle = bortle_low + (mpsas - mpsas_low) * (bortle_high - bortle_low) / (mpsas_high - mpsas_low)
            return round(bortle, 1)

# Convert radiance to magnitudes per square arcsecond
# This formula assumes the radiance is measured in the V band (visual magnitude) with a wavelength around 550 nm. 
# The constant 20.7233 is derived from the definition that a surface brightness of 0 mpsas
# corresponds to a radiance of 4.0 x 10^-8 W/cm2/sr in the V band.
def radianceToMpsas(radiance):
    return -2.5 * np.log10(radiance) + 20.7233

# Function to export the extracted data to a CSV file
def export_csv(data, filename):

    #if the filename extension is not .csv we add it to the filename
    if not filename.endswith(".csv"):
        filename += ".csv"

    with open(filename, 'w') as file:
        file.write('Latitude;Longitude;Radiance;mpsas;Bortle\n')
        for row in data:
            latitude = row[0]
            longitude = row[1]
            radiance = row[2]
            
            mpsas = radianceToMpsas(radiance)

            # Convert mpsas to Bortle scale on a homemade continuous scale with 0.1 precision, 
            # simply to have a better understanding of the light pollution level.
            bortle = mpsasToBortle(mpsas)
            file.write(f'{latitude};{longitude};{radiance};{mpsas};{bortle}\n')
    return filename

import json

# Function to export the extracted data to a GeoJSON file
def export_geojson(data, filename):
    # If the filename extension is not .geojson, add it to the filename
    if not filename.endswith(".json"):
        filename += ".json"

    features = []
    for row in data:
        latitude = float(row[0])
        longitude = float(row[1])
        radiance = float(row[2])

        mpsas = radianceToMpsas(radiance)
        bortle = mpsasToBortle(mpsas)

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [longitude, latitude]
            },
            "properties": {
                "Radiance": radiance,
                "mpsas": mpsas,
                "Bortle": bortle
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(filename, 'w') as file:
        json.dump(geojson, file, indent=0)

    return filename

# Function to compress a file using gzip
def gzip_file(filename, gzip_filename, verbose):
    with open(filename, 'rb') as f_in:
        with gzip.open(gzip_filename, 'wb', 9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    log(f"File compressed to {gzip_filename}", verbose)

def zip_file(filename, zip_filename, verbose):
    with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        zipf.write(filename)
    log(f"File compressed to {zip_filename}", verbose)

# Function to log an info message
def log(message, verbose):
    if verbose:
        console.print(f"[info]INFO:[/info] {message}")

# Function to log an error message and exit the program
def error(message):
    console.print(f"[error]ERROR:[/error] {message}")
    exit(1)

#Function to fotmat the number with the user locale
def format_number(number):
    return locale.format_string("%.f", number, grouping=True)

# Function to log the size and format of the exported data
def log_export_data(format, size):
    return(f"Exporting data to {format} file with {format_number(size)} recorded coordinates.")

# Function to ask the user if they want to extract data for the whole Spain or for specific regions
def process_spain_regions():
    console.print("Do you want to extract data for the whole Spain or for specific regions?")
    console.print("1. Whole Spain")
    console.print("2. Specific regions")
    choice = console.input("Enter your choice (1/2): ")
    if choice == "1":
        return COUNTRIES_DATA["ESP"]
    elif choice == "2":
        console.print("Select the region you want to extract data for:")
        console.print("1. Canary Islands")
        console.print("2. Balearic Islands")
        console.print("3. Spanish Peninsula")
        region_choice = console.input("Enter your choice (1/2/3): ")
        if region_choice == "1":
            return COUNTRIES_DATA["ESP_CANARY"]
        elif region_choice == "2":
            return COUNTRIES_DATA["ESP_BALEARIC"]
        elif region_choice == "3":
            return COUNTRIES_DATA["ESP_PENINSULA"]
        else:
            error("Error: Invalid region choice.")
            return None
    else:
        error("Error: Invalid choice.")
        return None

# Function to extract data from the raster file
def process_range_data(raster, min_row, max_row, min_col, max_col, sampling_interval, origin_x, origin_y, pixel_width, pixel_height, verbose):
    total_iterations = ((max_row - min_row + 1) // sampling_interval) * ((max_col - min_col + 1) // sampling_interval)
    range_data = []

    if verbose:
        with Progress() as progress:
            task = progress.add_task("[progress]Extracting data...", total=total_iterations)

            for i in range(min_row, max_row + 1, sampling_interval):
                for j in range(min_col, max_col + 1, sampling_interval):
                    # Calculate the geographic coordinates of the current pixel
                    x = origin_x + j * pixel_width
                    y = origin_y + i * pixel_height
                    
                    # Read the light pollution value at the current pixel
                    data = raster.ReadAsArray(j, i, 1, 1)
                    light_pollution = data[0, 0]
                    
                    # Append the data to the list if light pollution is not zero
                    if light_pollution > 0.0:
                        range_data.append([y, x, light_pollution])
                    
                    progress.update(task, advance=1)
    else:
        for i in range(min_row, max_row + 1, sampling_interval):
                for j in range(min_col, max_col + 1, sampling_interval):
                    # Calculate the geographic coordinates of the current pixel
                    x = origin_x + j * pixel_width
                    y = origin_y + i * pixel_height
                    
                    # Read the light pollution value at the current pixel
                    data = raster.ReadAsArray(j, i, 1, 1)
                    light_pollution = data[0, 0]
                    
                    # Append the data to the list if light pollution is not zero
                    if light_pollution > 0.0:
                        range_data.append([y, x, light_pollution])

    return range_data


# Main function to extract radiance data from a raster file and export it to a CSV file
def main():

    parser = argparse.ArgumentParser(description='Extract light pollution data from a GeoTIFF file.')
    parser.add_argument('input_file', help='Path to the input GeoTIFF file')
    parser.add_argument('--minlat', type=float, help='Minimum latitude of the bounding box')
    parser.add_argument('--maxlat', type=float, help='Maximum latitude of the bounding box')
    parser.add_argument('--minlon', type=float, help='Minimum longitude of the bounding box')
    parser.add_argument('--maxlon', type=float, help='Maximum longitude of the bounding box')
    parser.add_argument('--sampling', type=float, default=0.5, help='Sampling interval in kilometers')
    parser.add_argument('--outfile', default='output', help='Path to the output file with no extension')
    parser.add_argument('--outformat', default='CSV', choices=["CSV", "GeoJSON", "XML"], help='Output format (CSV, GeoJSON, XML)')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
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

    #if the args.input_file file does not exist, return an error.
    if not os.path.exists(args.input_file):
        error("The input file does not exist.")
        return

    if(args.sampling < 0.5):
        error("Sampling interval must be greater or equal than 0.5km. The GeoTIFF image has 15 arcseconds for each pixel")
        return

    raster = gdal.Open(args.input_file, gdal.OF_RASTER)

    if raster is None:
        error("Could not open the raster file.", args.verbose)
    else:
        log("Raster file opened successfully.", args.verbose)
    
        # Get the geotransform information
        geotransform = raster.GetGeoTransform()
        origin_x = geotransform[0] # Top left x
        origin_y = geotransform[3] # Top left y
        pixel_width = geotransform[1] # W-E pixel resolution
        pixel_height = geotransform[5] # N-S pixel resolution
        
        # Get the number of rows and columns in the raster
        cols = raster.RasterXSize # Number of columns
        rows = raster.RasterYSize # Number of rows
        log(f"Number of rows: {rows:n}, Number of columns: {cols:n}", args.verbose)
        

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
        
        # Calculate the pixel indices for Spain's bounding box
        min_col = int((min_lon - origin_x) / pixel_width)
        max_col = int((max_lon - origin_x) / pixel_width)
        min_row = int((origin_y - max_lat) / abs(pixel_height))
        max_row = int((origin_y - min_lat) / abs(pixel_height))
        
        #Calculate the number of pixels corresponding to 0.5km
        km_to_arcseconds = args.sampling * 3600 / 111.32  # Convert to arcseconds
        sampling_interval = int(km_to_arcseconds / 15)  # Divide by 15 arcseconds per pixel

        #The region name should be in the country_data dictionary or in the passed arguments
        region_name = country_data.get("Name") if country_data else "Custom region"

        log(f"Sampling interval: {sampling_interval}px for {args.sampling:.2f}km in {region_name}, {km_to_arcseconds:.3f} arcseconds for the interval", args.verbose)

        # Create a list to store the extracted data. Each element is a list with the latitude, longitude, and radiance values
        range_data = process_range_data(raster, min_row, max_row, min_col, max_col, sampling_interval, origin_x, origin_y, pixel_width, pixel_height, args.verbose)
        
        #Export the extracted data to a CSV file
        size = len(range_data)

        filename = args.outfile

        if args.outformat == "CSV":
            if args.verbose:
                with console.status(log_export_data("CSV", size)):
                    filename = export_csv(range_data, filename)
            else:
                filename = export_csv(range_data, filename)

        if args.outformat == "GeoJSON":
            if args.verbose:
                with console.status(log_export_data("GeoJSON", size)):
                    filename = export_geojson(range_data, filename)
            else:
                filename = export_geojson(range_data, filename)
        
        log("Data extraction and export completed successfully.", args.verbose)

        if args.gzip:
            if args.verbose:
                with console.status("Compressing the file with gzip..."):
                    gzip_file(filename, f"{filename}.gz", args.verbose)
            else:
                gzip_file(filename, f"{filename}.gz", args.verbose)

        if args.zip:
            if args.verbose:
                with console.status("Compressing the file with zip..."):
                    zip_file(filename, f"{filename}.zip", args.verbose)
            else:
                zip_file(filename, f"{filename}.zip", args.verbose)


if __name__ == '__main__':
    main()
