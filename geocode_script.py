import json
import time
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Initialize the geocoder
geolocator = Nominatim(user_agent="gemini_cli_map_geocoder_v3")
# Use a rate limiter to respect Nominatim's usage policy (1 request per second)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, error_wait_seconds=5, max_retries=2)

input_filename = 'travel_data.json'
output_filename = 'travel_data.json' # Overwrite the original file

print(f"Reading data from {input_filename}...")

try:
    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error reading {input_filename}: {e}")
    exit()

locations = data.get('locations', [])
if not locations:
    print("No locations found in the JSON file.")
    exit()

total_locations = len(locations)
locations_to_process = []

# Find locations that need geocoding
for loc in locations:
    if loc.get('lat') is None or loc.get('lon') is None or loc.get('country') is None:
        locations_to_process.append(loc)

if not locations_to_process:
    print("All locations already have full coordinate and country data. Nothing to do.")
    exit()

print(f"Found {len(locations_to_process)} locations that need geocoding.")

for i, location in enumerate(locations_to_process):
    place_name = location.get('place')
    if not place_name:
        print(f"({i+1}/{len(locations_to_process)}) Skipping a location because it has no 'place' name.")
        continue

    try:
        print(f"({i+1}/{len(locations_to_process)}) Geocoding '{place_name}'...")
        geo_result = geocode(place_name, language='en')
        
        if geo_result:
            location['lat'] = geo_result.latitude
            location['lon'] = geo_result.longitude
            
            try:
                country = geo_result.address.split(',')[-1].strip()
                location['country'] = country
                print(f"  -> Success: ({geo_result.latitude:.4f}, {geo_result.longitude:.4f}) - Country: {country}")
            except (IndexError, AttributeError) as addr_e:
                location['country'] = None # Set country to None if parsing fails
                print(f"  -> Success, but could not parse country from address: {geo_result.address}. Error: {addr_e}")

        else:
            # Mark as failed by setting country to a specific string, so we don't re-process it every time
            location['country'] = "Geocoding Failed"
            print(f"  -> Failed: Could not find coordinates for '{place_name}'. Marked as failed.")

    except Exception as e:
        print(f"An error occurred while geocoding '{place_name}': {e}")
        location['country'] = "Geocoding Error"

# Save the updated data (the full list, including unchanged items)
data['locations'] = locations
try:
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSuccessfully updated {output_filename}!")
except IOError as e:
    print(f"\nError writing to {output_filename}: {e}")
