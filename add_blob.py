# utility script to manually add a blob
import constants

import sys
import os
import requests

# initialize global variables
HOST = os.getenv("HOST", constants.SERVER_DEFAULTS["HOST"])
PORT = os.getenv("PORT", constants.SERVER_DEFAULTS["PORT"])

HOST = "https://ripe-staging.herokuapp.com"

blob_path = str(sys.argv[1])
blob_name = os.path.basename(blob_path)
endpoint = constants.SERVER_ENDPOINTS["POST_BLOB"]

blob = open(blob_path, "rb").read()
files = {
    "blob": blob
}

args = {
    "blob_name": blob_name
}

url = "https://ripe-staging.herokuapp.com" + endpoint
print "posting {} to {}".format(blob_path, url)
response = requests.post(url=url, files=files, params=args)
print response, response.content