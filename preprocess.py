import os
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv


session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
s3_client = session.client("s3")

import re


def make_filename_compatible(name):
    # Replace unwanted characters with an underscore or any other character of your choice
    sanitized_name = re.sub(
        r'[\\/*?:"<>|()\'&]', "_", name
    )  # Including parentheses in the pattern

    sanitized_name = re.sub(
        r"\s+", "_", sanitized_name
    )  # Replacing spaces with underscore
    return sanitized_name


def upload_to_s3(file_name, bucket, object_name=None):
    """
    Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified, file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        print(response)
    except NoCredentialsError:
        print("Credentials not available")
        return False
    return True


def get_s3_public_url(bucket_name, object_key):
    """
    Construct the public URL for an object in an S3 bucket.

    :param bucket_name: Name of the S3 bucket
    :param object_key: Object key in the S3 bucket
    :return: Public URL as a string
    """
    return f"https://{bucket_name}.s3.amazonaws.com/{object_key}"


new_data = []
with open("metadata2.txt", "r") as file:
    for line in file:
        url, name = line.strip().split(", ")
        count_names = name.split(" - ")
        if len(count_names) >= 2:
            name = count_names[1]

        rename = name.replace(" ", "_")
        rename = make_filename_compatible(rename)
        try:
            command = f"yt-dlp -x --audio-format mp3 '{url}' -o raw_music/{rename}.mp3"
            os.system(command)

            uploaded = upload_to_s3(
                f"raw_music/{rename}.mp3",
                "taylor-raw",
            )
            if uploaded:
                print("File uploaded successfully.")
            else:
                print("Upload failed.")

            new_data.append(
                (get_s3_public_url("taylor-raw", f"raw_music/{rename}.mp3"), name)
            )
        except Exception as e:
            print(f"ERROR: {e}")


with open("metadata2_reformatted.txt", "w") as file:
    for path, name in new_data:
        file.write(f"{path}, {name}\n")
