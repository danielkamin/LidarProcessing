import subprocess
import json
from pyproj import CRS

def epsg_code(metadata):
    try:
        epsg_code = None
        srsWKT = metadata['metadata']['srs']['horizontal']
        srsCRS = CRS.from_wkt(srsWKT)

        epsg_code = srsCRS.to_epsg()

        if not epsg_code:
            raise ValueError("EPSG code not found in the metadata. Stopping the script.")
        return epsg_code
    except subprocess.CalledProcessError as e:
        print(e)

def extract_metadata(las_file):
    try:
        # Construct the laszip command
        command = ['pdal', 'info', '--metadata', las_file]
        metadata_json = subprocess.check_output(command).decode('utf-8')
        metadata = json.loads(metadata_json)
        # Run the command
        print(f"Successfully extracted metadata from {las_file}")
        return metadata
    except subprocess.CalledProcessError as e:
        print(f"Error extracting metadata from {las_file}: {e}")
        return None