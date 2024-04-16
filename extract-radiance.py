import argparse
from osgeo import gdal
import numpy as np
import gzip
import shutil
import zipfile

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

# Function to export the extracted data to a CSV file
def export_csv(data, filename):

    with open(filename, 'w') as file:
        file.write('Latitude;Longitude;Radiance;mpsas;Bortle\n')
        for row in data:
            latitude = row[0]
            longitude = row[1]
            radiance = row[2]

            # Convert radiance to magnitudes per square arcsecond
            # This formula assumes the radiance is measured in the V band (visual magnitude) with a wavelength around 550 nm. 
            # The constant 20.7233 is derived from the definition that a surface brightness of 0 mpsas
            # corresponds to a radiance of 4.0 x 10^-8 W/cm2/sr in the V band.
            mpsas = -2.5 * np.log10(radiance) + 20.7233

            # Convert mpsas to Bortle scale on a homemade continuous scale with 0.1 precision, 
            # simply to have a better understanding of the light pollution level.
            bortle = mpsasToBortle(mpsas)
            file.write(f'{latitude};{longitude};{radiance};{mpsas};{bortle}\n')
  
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

def log(message, verbose):
    if verbose:
        print(message)


# Main function to extract radiance data from a raster file and export it to a CSV file
def main():

    parser = argparse.ArgumentParser(description='Extract light pollution data from a GeoTIFF file.')
    parser.add_argument('input_file', help='Path to the input GeoTIFF file')
    parser.add_argument('--min_lat', type=float, default=35.947, help='Minimum latitude of the bounding box')
    parser.add_argument('--max_lat', type=float, default=43.749, help='Maximum latitude of the bounding box')
    parser.add_argument('--min_lon', type=float, default=-9.393, help='Minimum longitude of the bounding box')
    parser.add_argument('--max_lon', type=float, default=3.040, help='Maximum longitude of the bounding box')
    parser.add_argument('--sampling_interval', type=float, default=0.5, help='Sampling interval in kilometers')
    parser.add_argument('--output_file', default='output.csv', help='Path to the output CSV file')
    parser.add_argument('--output-format', default='CSV', choices=["CSV", "GeoJSON", "XML"], nargs=3, help='Output format (CSV, GeoJSON, XML)')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--gzip', action="store_true",  help='Compress the output file with gzip')
    group.add_argument('--zip' , action='store_true', help='Compress the output file with zip')

    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument('--verbose', action='store_true', help='Print verbose output')
    group2.add_argument('--quiet', action='store_true', help='Suppress all output')

    args = parser.parse_args()

    raster = gdal.Open(args.input_file, gdal.OF_RASTER)

    if raster is None:
        log("Error: Could not open the raster file.", args.verbose)
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
        log(f"Number of rows: {rows}, Number of columns: {cols}", args.verbose)
        
        # Define the bounding box for Spain
        min_lat, max_lat,min_lon, max_lon = args.min_lat, args.max_lat, args.min_lon, args.max_lon
        
        # Calculate the pixel indices for Spain's bounding box
        min_col = int((min_lon - origin_x) / pixel_width)
        max_col = int((max_lon - origin_x) / pixel_width)
        min_row = int((origin_y - max_lat) / abs(pixel_height))
        max_row = int((origin_y - min_lat) / abs(pixel_height))
        
        #Calculate the number of pixels corresponding to 0.5km
        km_to_arcseconds = args.sampling_interval * 3600 / 111.32  # Convert to arcseconds
        sampling_interval = int(km_to_arcseconds / 15)  # Divide by 15 arcseconds per pixel
        log(f"Sampling interval: {sampling_interval}px for {args.sampling_interval}km in Spain.\n {km_to_arcseconds:.3f} arcseconds for {args.sampling_interval}km", args.verbose)

        # Create a list to store the extracted data for Spain
        range_data = []
        
        # Iterate over the pixels within Spain's bounding box
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
        
        #Export the extracted data to a CSV file
        if(args.output_format == "CSV"):
            log(f"Exporting data to CSV file with {len(range_data)} recorded coordinates.", args.verbose)
            export_csv(range_data, args.output_file)
        log("Data extraction and export completed successfully.", args.verbose)

        #gzip the file
        if(args.gzip):
            log("Compressing the file with gzip...", args.verbose)
            gzip_file(args.output_file, f"{args.output_file}.gz", args.verbose)
        if(args.zip):
            log("Compressing the file with zip...", args.verbose)
            zip_file(args.output_file, f"{args.output_file}.zip", args.verbose)

if __name__ == '__main__':
    main()
