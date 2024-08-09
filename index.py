import os
import argparse
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import decompress #internal
import extract_info #internal
import matplotlib.pyplot as plt
import numpy as np
import rasterio

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--InputLazFile", help = "Show Output")
parser.add_argument("-o", "--OutputLasFile", help = "Show Output")
args = parser.parse_args()

if args.InputLazFile == None or args.OutputLasFile == None:
   raise RuntimeError("Invalid arguments")

LIDAR_DATA_BASE_PATH = './Data/lidar'
INPUT_LAZ_FILE_PATH = os.path.join(LIDAR_DATA_BASE_PATH, 'laz', args.InputLazFile + '.laz')
OUTPUT_LAS_FILE_PATH =  os.path.join(LIDAR_DATA_BASE_PATH, 'las', args.OutputLasFile + '.las')

if os.path.isfile(OUTPUT_LAS_FILE_PATH) == False:
   decompress.laz_to_las(INPUT_LAZ_FILE_PATH, OUTPUT_LAS_FILE_PATH)

metadata = extract_info.extract_metadata(OUTPUT_LAS_FILE_PATH)
epsg = extract_info.epsg_code(metadata)

os.environ['GISBASE'] = '/opt/local/lib/grass83'  # Path to GRASS GIS base
os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.path.join(os.environ['GISBASE'], 'bin')
os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.path.join(os.environ['GISBASE'], 'scripts')
os.environ['LD_LIBRARY_PATH'] = os.path.join(os.environ['GISBASE'], 'lib')
os.environ['GISDBASE'] = '/Users/danielkaminski/Desktop/Magisterka/Program/Data'  # Path to GRASS database
os.environ['GRASSBIN'] = 'grass83'  # GRASS binary

grass_python_path = '/opt/local/lib/grass83/etc/python'  # Adjust this path if needed
sys.path.append(grass_python_path)

import grass.script as gs # type: ignore

location = epsg
mapset = 'PERMANENT'
gisdb = os.environ['GISDBASE']
geo_tiff_output = 'yearly_rad.tif'

if os.path.exists(geo_tiff_output):
  os.remove(geo_tiff_output)

if not os.path.exists(os.path.join(gisdb, str(location))):
    subprocess.call(['grass', '-c', 'EPSG:'+str(location), '-e', os.path.join(gisdb, str(location))])

rcfile = gs.setup.init(os.path.join(gisdb, str(location), mapset))

gs.run_command('v.in.lidar', input=OUTPUT_LAS_FILE_PATH, output='lidar_points', overwrite=True)
gs.run_command('g.region', vector='lidar_points')
gs.run_command('v.surf.rst', input='lidar_points', elevation='dem', overwrite=True)

# Function to run r.sun for a given day
def calculate_daily_radiation(day):
    gs.run_command('r.sun', elevation='dem', quiet=True, glob_rad=f'global_rad_{day}', day=day, overwrite=True)

# Parallel processing of daily solar radiation
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(calculate_daily_radiation, day) for day in range(1, 366)]
    for future in as_completed(futures):
        try:
            future.result()  # This will raise any exceptions caught during execution
        except Exception as e:
            print(f"Error processing day {futures.index(future)+1}: {e}")

gs.run_command('r.series', input=[f'global_rad_{day}' for day in range(1, 366)], output='yearly_rad', method='sum', overwrite=True)

gs.read_command('r.out.gdal', input='yearly_rad', flags='c', format='GTiff', output=geo_tiff_output, overwrite=True)

with rasterio.open(geo_tiff_output) as src:
    data = src.read(1)
    profile = src.profile

plt.figure(figsize=(10, 10))
plt.imshow(data, cmap='hot', interpolation='nearest')
plt.colorbar(label='Solar Radiation (Wh/m^2)')
plt.title('Yearly Solar Radiation')
plt.xlabel('Easting')
plt.ylabel('Northing')
plt.show()

# Check if the folder exists and save the image
image_folder = f'./Images/{epsg}'
if not os.path.exists(image_folder):
    os.makedirs(image_folder)
image_path = os.path.join(image_folder, 'yearly_solar_radiation.png')
plt.savefig(image_path)

plt.show()