from osgeo import gdal
import numpy as np
import gzip
import shutil

def is_in_spain(lat, lon):
    # Approximate bounding box for Spain
    # 'ES': ('Spain', (-9.39288367353, 35.946850084, 3.03948408368, 43.7483377142)),
    min_lat, max_lat = 35.947, 43.749
    min_lon, max_lon = -9.393, 3.040
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon

def mpsasToBortle(mpsas):
    mpsas_ranges = [21.89, 21.69, 21.25, 20.49, 19.50, 18.94, 18.38, 17.80]
    bortle_values = [1, 2, 3, 4, 5, 6, 7, 8, 9]

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

def export_csv(data, filename):

    with open(filename, 'w') as file:
        file.write('Latitude;Longitude;Radiance;mpsas;Bortle\n')
        for row in data:
            if float(row[2]) > 0.0:
                latitude = row[0]
                longitude = row[1]
                radiance = row[2]
                # Convert radiance to magnitudes per square arcsecond
                # This formula assumes the radiance is measured in the V band (visual magnitude) with a wavelength around 550 nm. 
                # The constant 20.7233 is derived from the definition that a surface brightness of 0 mpsas
                # corresponds to a radiance of 4.0 x 10^-8 W/cm2/sr in the V band.
                mpsas = -2.5 * np.log10(radiance) + 20.7233

                # Convert mpsas to Bortle scale on a homemade continuous scale with 0.1 precision, simply to have a better understanding of the light pollution level.
                bortle = mpsasToBortle(mpsas)
                file.write(f'{latitude};{longitude};{radiance};{mpsas};{bortle}\n')
  

def gzip_file(filename, gzip_filename):
    with open(filename, 'rb') as f_in:
        with gzip.open(gzip_filename, 'wb', 9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"File compressed to {gzip_filename}")


raster = gdal.Open('test.tif', gdal.OF_RASTER)

if raster is None:
    print("Error: Could not open the raster file.")
else:
    print("Raster file opened successfully.")
    
    # Get the number of bands in the raster
    num_bands = raster.RasterCount
    print(f"Number of bands: {num_bands}")
    
    # Get the geotransform information
    geotransform = raster.GetGeoTransform()
    origin_x = geotransform[0]
    origin_y = geotransform[3]
    pixel_width = geotransform[1]
    pixel_height = geotransform[5]
    
    # Get the number of rows and columns in the raster
    cols = raster.RasterXSize
    rows = raster.RasterYSize
    print(f"Number of rows: {rows}, Number of columns: {cols}")
    
    # Define the bounding box for Spain
    min_lat, max_lat = 35.947, 43.749
    min_lon, max_lon = -9.393, 3.040
    
    # Calculate the pixel indices for Spain's bounding box
    min_col = int((min_lon - origin_x) / pixel_width)
    max_col = int((max_lon - origin_x) / pixel_width)
    min_row = int((origin_y - max_lat) / abs(pixel_height))
    max_row = int((origin_y - min_lat) / abs(pixel_height))
    
    #Calculate the number of pixels corresponding to 0.5km
    km_to_arcseconds = 0.5 * 3600 / 111.32  # Convert to arcseconds
    sampling_interval = int(km_to_arcseconds / 15)  # Divide by 15 arcseconds per pixel
    print(f"Sampling interval: {sampling_interval}px for 0.5km in Spain. {km_to_arcseconds:.3f} arcseconds for 0.5km")

    # Create a list to store the extracted data for Spain
    spain_data = []
    
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
                spain_data.append([y, x, light_pollution])
    
    #Export the extracted data to a CSV file
    print(f"Exporting data to CSV file with {len(spain_data)} recorded coordinates.");
    export_csv(spain_data, 'ES.csv')
    print("Data extraction and export completed successfully.")

    #gzip the file
    print("Compressing the file...")
    gzip_file('ES.csv', 'ES.csv.gz')
