# Light Pollution Data Extraction

This Python script extracts light pollution data from a GeoTIFF file for a specified region and exports the data to a CSV file. The script uses the GDAL library to read the GeoTIFF file and performs calculations to convert the radiance values to magnitudes per square arcsecond (mpsas) and the Bortle scale.

## Prerequisites

- Python 3.x
- numpy library
- GDAL library
  - On Windows, it is recommended to install GDAL using Conda. Other operating systems may be able to install it directly using pip.
- The GeoTIFF file containing the light pollution data

To install the required libraries, run the following commands:

```bash
conda create -n geotiff gdal python pip
```

or use requirements.txt:

```bash
pip install -r requirements.txt
```

or use conda:

```bash
conda env create -f environment.yml
```

## Data Source

The GeoTIFF files used in this script are obtained from the [Earth Observation Group (EOG)](https://payneinstitute.mines.edu/eog/) at the Payne Institute for Public Policy. The data is part of the [VIIRS Nighttime Lights](https://eogdata.mines.edu/products/vnl/) product.

Please cite EOG as the data source and refer to the relevant papers for the specific EOG product you are using. 
Many of the VIIRS Nighttime Lights data are available under the [Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/). 
For further details, please refer to the document [here](https://eogdata.mines.edu/files/EOG_products_CC_License.pdf).

## Usage

1. Download the desired GeoTIFF file from the EOG data source.
2. Run the script using the command: 

```bash
python extract_radiance.py input_file [--min_lat MIN_LAT] [--max_lat MAX_LAT] [--min_lon MIN_LON] [--max_lon MAX_LON] [--sampling_interval SAMPLING_INTERVAL] [--output_file OUTPUT_FILE] [--output-format {CSV,GeoJSON,XML} [{CSV,GeoJSON,XML} ...]] [--gzip | --zip] [--verbose | --quiet]
```
- `input_file`: Path to the input GeoTIFF file.
- `--min_lat MIN_LAT`: Minimum latitude of the bounding box (default: 35.947).
- `--max_lat MAX_LAT`: Maximum latitude of the bounding box (default: 43.749).
- `--min_lon MIN_LON`: Minimum longitude of the bounding box (default: -9.393).
- `--max_lon MAX_LON`: Maximum longitude of the bounding box (default: 3.040).
- `--sampling_interval SAMPLING_INTERVAL`: Sampling interval in kilometers (default: 0.5).
- `--output_file OUTPUT_FILE`: Path to the output CSV file (default: output.csv).
- `--output-format {CSV,GeoJSON,XML} [{CSV,GeoJSON,XML} ...]`: Output format (CSV, GeoJSON, XML) (default: CSV).
- `--gzip`: Compress the output file with gzip.
- `--zip`: Compress the output file with zip.
- `--verbose`: Print verbose output.
- `--quiet`: Suppress all output.
3. The script will extract the light pollution data for the specified region and export it to the chosen output format.
4. If the `--gzip` or `--zip` option is used, the script will compress the output file using the respective compression method.

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

- The [Earth Observation Group (EOG)](https://payneinstitute.mines.edu/eog/) at the Payne Institute for Public Policy for providing the VIIRS Nighttime Lights data.
- The [GDAL library](https://github.com/OSGeo/gdal) for enabling the reading and processing of GeoTIFF files.
