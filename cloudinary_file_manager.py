"""
Module handles uploading and downloading files from the Cloudinary website.
"""
import cloudinary
import cloudinary.uploader
import logging
from dotenv import load_dotenv
import os
import requests

# setup error logging capture
logger = logging.getLogger("wct_mobile_app")

# load the Cloudinary credentials from the .eng file
load_dotenv()

# assign the Cloudinary credentials to variables.
cloud_name = "CLOUDINARY_CLOUD_NAME"
api_key = "CLOUDINARY_API_KEY"
api_secret = "CLOUDINARY_API_SECRET"


def UPLOAD_FILE_TO_CLOUDINARY(image_data, public_id, file_type):
    """
    Function will connect to the Cloudinary file store and upload the file into the appropriate location with the
    appropriate file name.  The location is determined based on the file_type.
    :param image_data: the data to be uploaded to Cloudinary
    :param public_id: the name of the file in Web Cost Tracker and Cloudinary
    :param file_type: the type of file to be uploaded (e.g., photos, miscellaneous, or error logs)
    :return:
    """
    logger.info("")
    logger.info("---------------------------------------------------------------------------")
    logger.info("STARTING UPLOAD_FILE_TO_CLOUDINARY EVENT")
    logger.info(f"ATTEMPTING TO UPLOAD FILE: {public_id} OF TYPE: {file_type} TO CLOUDINARY")

    logger.info(f"Attempting to read environment variable cloud name: {cloud_name} from .env file.")
    cloudinary_cloud = os.getenv(cloud_name)
    if not cloudinary_cloud:
        logger.error(f"CRITICAL: Cloud: {cloud_name} was NOT found or is empty in the .env file.")
        return None
    logger.info(f"Cloud: {cloud_name} was successfully retrieved from the .env file.")

    logger.info(f"Attempting to read environment variable api key: {api_key} from .env file.")
    cloudinary_api_key = os.getenv(api_key)
    if not cloudinary_api_key:
        logger.error(f"CRITICAL: Key: {api_key} was NOT found or is empty in the .env file.")
        return None
    logger.info(f"Key: {api_key} was successfully retrieved from the .env file.")

    logger.info(f"Attempting to read environment variable api secret: {api_secret} from .env file.")
    cloudinary_api_secret = os.getenv(api_secret)
    if not cloudinary_api_secret:
        logger.error(f"CRITICAL: Secret: {api_secret} was NOT found or is empty in the .env file.")
        return None
    logger.info(f"Secret: {api_key} was successfully retrieved from the .env file.")

    logger.info("")
    logger.info("Configure Cloudinary with the retrieved credentials.")
    cloudinary.config(
        cloud_name=cloudinary_cloud,
        api_key=cloudinary_api_key,
        api_secret=cloudinary_api_secret,
        secure=True
    )

    logger.info("")
    logger.info("Generate the appropriate Cloudinary subfolder and Cloudinary resource type based on the file type  "
                "being uploaded to Cloudinary")
    # folders in cloudinary are Invoices, Error_Logs, and Photos
    if file_type == "photos":
        # files stored are photos typically from mobile app camera
        subfolder = "/Photos"
        resource = "image"
    elif file_type == "miscellaneous":
        # files stored are typically PDF uploaded from email
        subfolder = "/Miscellaneous"
        resource = "raw"
    else:
        # files stored are text files from the python logger
        subfolder = "/Error_Logs"
        resource = "raw"
    logger.info("File type = ", file_type)
    logger.info("Cloudinary subfolder = ", subfolder)
    logger.info("Cloudinary resource = ", resource)

    logger.info("")
    logger.info(f"Attempt to connect to Cloudinary and upload file: {public_id} to Cloudinary subfolder: {subfolder}")
    try:
        # define the file to be uploaded, the upload location, and attempt to upload
        response = cloudinary.uploader.upload(
            image_data,
            folder=subfolder,
            public_id=public_id,
            overwrite=True,
            resource_type=resource
        )
        logger.info(f"Successfully uploaded file: {public_id} to Cloudinary subfolder: {subfolder}")
        logger.info(f"Successfully uploaded {response.get('resource_type')}: {public_id}. "
                    f"Format: {response.get('format')}, Size: {response.get('bytes')} bytes. "
                    f"URL: {response.get('secure_url')}")
        upload_successful = True
        return upload_successful

    # Catch specific Cloudinary API/Configuration errors
    except cloudinary.exceptions.Error as ce:
        logger.error(f"Cloudinary API error during upload of {public_id}: {ce}")
        return False

    # Catch network-level timeouts or connection failures
    except (requests.exceptions.RequestException, ConnectionError) as ne:
        logger.error(f"Network error connecting to Cloudinary for file {public_id}: {ne}")
        return False

    # Catch all other unexpected Python runtime errors (e.g., NameError, TypeError)
    except Exception as e:
        logger.error(f"Unexpected error uploading file {public_id}: {e}", exc_info=True)
        return False
