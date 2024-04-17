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
python extract_radiance.py input_file [--minlat MIN_LAT] [--maxlat MAX_LAT] [--minlon MIN_LON] [--maxlon MAX_LON] [--sampling SAMPLING_INTERVAL] [--outfile OUTPUT_FILE] [--outformat {CSV,GeoJSON,XML} [{CSV,GeoJSON,XML} ...]] [--gzip | --zip] [--verbose | --quiet]
```
- `input_file`: Path to the input GeoTIFF file.
- `--minlat MIN_LAT`: Minimum latitude of the bounding box.
- `--maxlat MAX_LAT`: Maximum latitude of the bounding box.
- `--minlon MIN_LON`: Minimum longitude of the bounding box.
- `--maxlon MAX_LON`: Maximum longitude of the bounding box.
- `--sampling SAMPLING_INTERVAL`: Sampling interval in kilometers (default: 0.5). This the distance between each data point in the output file.
      - For example, if the sampling interval is 0.5 km, the script will extract data points every 0.5 km in both the latitude and longitude directions.
      - The minimum sampling interval is 0.5 km due to technical limitations. Each pixel in the GeoTIFF file represents a 15 arcsec area, around 0.5 km x 0.5 km.

- `--outfile OUTPUT_FILE`: Path to the output file with no extension (default: output).
- `--outformat {CSV,GeoJSON,XML} [{CSV,GeoJSON,XML} ...]`: Output format (CSV, GeoJSON, XML) (default: CSV).
- `--gzip`: Compress the output file with gzip.
- `--zip`: Compress the output file with zip.
- `--verbose`: Print verbose output.
- `--quiet`: Suppress all output.
- `--help`: Display the help message.
- `--version`: Display the version information.
- `--country`: Country code to extract the data for a specific country using the ISO 3166-1 alpha-3 code.
   - For example, to extract data for the United States, use `--country USA`.
   - The `--country` option will override the `--min_lat`, `--max_lat`, `--min_lon`, and `--max_lon` options.
   - The country code must be in uppercase.
   - The country code must be a valid ISO 3166-1 alpha-3 code.
   - The `countries.txt` file contains the list of valid country codes, names and bounding box coordinates.
   - If you see any error on the file please report it as an issue or create a pull request.
   
- `--quiet` will override `--verbose`. Both cannot be used together, and if none is used, the script will assign the default value of `--verbose`.

3. The script will extract the light pollution data for the specified region and export it to the chosen output format.
4. If the `--gzip` or `--zip` option is used, the script will compress the output file using the respective compression method.

## Output

The script generates two output files, e. g. if the `--outformat CSV` option is used:

1. `output.csv`: A CSV file containing the extracted light pollution data. Each row represents a data point with the following columns (if the option `--outformat CSV` is used):
   - Latitude
   - Longitude
   - Radiance
   - mpsas (magnitudes per square arcsecond)
   - Bortle (Bortle scale value)
2. `output.csv.gz`: A compressed version of the CSV file using gzip compression if the `--gzip` option is used.
3. `output.csv.zip`: A compressed version of the CSV file using zip compression if the `--zip` option is used.


## License

This script is released under the [MIT License](LICENSE).

## Acknowledgments

- The [Earth Observation Group (EOG)](https://payneinstitute.mines.edu/eog/) at the Payne Institute for Public Policy for providing the VIIRS Nighttime Lights data.
- The [GDAL library](https://github.com/OSGeo/gdal) for enabling the reading and processing of GeoTIFF files.
- The [numpy library](https://numpy.org/) for numerical computing in Python.
- [This comment](https://gist.github.com/graydon/11198540?permalink_comment_id=2702247#gistcomment-2702247) from a GitHub Gist that provided the list of ISO 3166-1 alpha-3 country codes and bounding boxes.

