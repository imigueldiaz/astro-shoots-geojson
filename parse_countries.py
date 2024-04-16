import json
# Open the txt file
with open("countries.txt", "r") as file:
    # Read the lines from the file
    lines = file.readlines()

# Remove the header line
lines = lines[1:]

# Create a dictionary to store the country data
countries_data = {}

# Iterate over each line
for line in lines:
    # Split the line by semicolon
    fields = line.strip().split(";")
    
    # Extract the values from the fields
    iso3 = fields[0]
    name = fields[1]
    lat_min = float(fields[2])
    lat_max = float(fields[3])
    lon_min = float(fields[4])
    lon_max = float(fields[5])
    
    # Create a dictionary for the country data
    country_data = {
        "Name": name,
        "lat_min": lat_min,
        "lat_max": lat_max,
        "lon_min": lon_min,
        "lon_max": lon_max
    }
    
    # Add the country data to the countries_data dictionary
    countries_data[iso3] = country_data

# Create additional objects for specific regions
canary_islands = {
    "Name": "Canary Islands",
    "lat_min": 27.6377389,
    "lat_max": 29.4160647,
    "lon_min": -18.1608733,
    "lon_max": -13.3364961
}

balearic_islands = {
    "Name": "Balearic Islands",
    "lat_min": 38.6434891,
    "lat_max": 40.0945909,
    "lon_min": 1.1282642,
    "lon_max": 4.3277839
}

spanish_peninsula = {
    "Name": "Spanish Peninsula",
    "lat_min": 36.0001819,
    "lat_max": 43.7902609,
    "lon_min": -9.3024255,
    "lon_max": 3.3136136
}

# Add the additional objects to the countries_data dictionary
countries_data["ESP_CANARY"] = canary_islands
countries_data["ESP_BALEARIC"] = balearic_islands
countries_data["ESP_PENINSULA"] = spanish_peninsula

# Create a new Python file
with open("countries_data.py", "w") as file:
    # Write the dictionary to the file
    file.write(f"COUNTRIES_DATA = {json.dumps(countries_data, indent=4)}")

print("countries_data.py file created successfully.")
