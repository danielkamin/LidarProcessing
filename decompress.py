import subprocess

def laz_to_las(input_laz, output_las):
    try:
        # Construct the laszip command
        command = ['pdal', 'translate', input_laz, output_las]
        
        # Run the command
        subprocess.run(command, check=True)
        print(f"Successfully decompressed {input_laz} to {output_las}")
    except subprocess.CalledProcessError as e:
        print(f"Error decompressing {input_laz}: {e}")
