# utility script to manually add an object FROM A FILE
import constants

import sys
import json
import os
import requests

# initialize global variables
HOST = os.getenv("HOST", constants.SERVER_DEFAULTS["HOST"])
PORT = os.getenv("PORT", constants.SERVER_DEFAULTS["PORT"])


file_path = str(sys.argv[2])
object_type = str(sys.argv[1])
endpoint = None
if object_type not in constants.OBJECT_TYPES:
    raise Exception("object_type must be one of {}".format(constants.OBJECT_TYPES.keys()))
else:
    endpoint = constants.SERVER_ENDPOINTS["POST_OBJ"].replace("<object_type>",
                                                             object_type)

with open(file_path, "r") as input:
    json_data = json.load(input)


# TODO: this is super fucking janky, but it's a util script, so do we really need to make it better?
url = "https://" + HOST + endpoint
print "posting {} to {}".format(file_path, url)
response = requests.post(url=url, json=json_data)
print response, response.content

