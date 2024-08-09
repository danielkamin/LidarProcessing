import boto3
import os
import argparse


def upload_to_s3(file_path, bucket_name, object_name=None):
    """Upload a file to an S3 bucket"""
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_path, bucket_name, object_name)
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False
    return True

def analyze_image_with_rekognition(bucket_name, object_name):
    """Analyze an image using Amazon Rekognition"""
    rekognition_client = boto3.client('rekognition')

    response = rekognition_client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': object_name
            }
        },
        MaxLabels=10,
        MinConfidence=75
    )
    
    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--InputImageFolder", help = "Show Output")
    args = parser.parse_args()
    if args.InputImageFolder == None:
        raise RuntimeError("Image missing")

    # Define the image path and S3 bucket details
    epsg = args.InputImageFolder
    image_folder = f'./Images/{epsg}'
    image_file = 'yearly_solar_radiation.png'
    file_path = os.path.join(image_folder, image_file)
    bucket_name = 'your-s3-bucket-name'  # Replace with your S3 bucket name
    object_name = f'{epsg}/{image_file}'  # S3 object name

    # Upload the image to S3
    if upload_to_s3(file_path, bucket_name, object_name):
        print(f"File {file_path} uploaded to S3 bucket {bucket_name} as {object_name}")

        # Analyze the image with Rekognition
        rekognition_response = analyze_image_with_rekognition(bucket_name, object_name)
        print("Rekognition response:")
        print(rekognition_response)
    else:
        print("Failed to upload the file to S3")