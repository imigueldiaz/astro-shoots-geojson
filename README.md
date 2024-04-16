# Light Pollution Data Extraction

This Python script extracts light pollution data from a GeoTIFF file for a specified region and exports the data to a CSV file. The script uses the GDAL library to read the GeoTIFF file and performs calculations to convert the radiance values to magnitudes per square arcsecond (mpsas) and the Bortle scale.

## Prerequisites

- Python 3.x
- GDAL library
  - On Windows, it is recommended to install GDAL using Conda. Other operating systems may be able to install it directly using pip.

## Data Source

The GeoTIFF files used in this script are obtained from the Earth Observation Group (EOG) at the Payne Institute for Public Policy. The data is part of the VIIRS Nighttime Lights product.

Please cite EOG as the data source and refer to the relevant papers for the specific EOG product you are using. Many of the VIIRS Nighttime Lights data are available under the Creative Commons Attribution 4.0 International license. For further details, please refer to the document [HERE](https://eogdata.mines.edu/products/vnl/).

## Usage

1. Download the desired GeoTIFF file from the EOG data source.
2. Update the following parameters in the script according to your requirements:
   - `min_lat`, `max_lat`, `min_lon`, `max_lon`: Bounding box coordinates for the region of interest.
   - `sampling_interval`: Sampling interval in pixels for extracting data points. Adjust this value based on the desired spatial resolution.
3. Run the script using the command: `python extract_radiance.py`
4. The script will extract the light pollution data for the specified region and export it to a CSV file named `output.csv`.
5. The script will also compress the CSV file using gzip compression and save it as `output.csv.gz`.

## Output

The script generates two output files:

1. `output.csv`: A CSV file containing the extracted light pollution data. Each row represents a data point with the following columns:
   - Latitude
   - Longitude
   - Radiance
   - mpsas (magnitudes per square arcsecond)
   - Bortle (Bortle scale value)
2. `output.csv.gz`: A compressed version of the CSV file using gzip compression.

## License

This script is released under the [MIT License](LICENSE).

## Acknowledgments

- The Earth Observation Group (EOG) at the Payne Institute for Public Policy for providing the VIIRS Nighttime Lights data.
- The GDAL library for enabling the reading and processing of GeoTIFF files.
