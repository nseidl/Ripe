import time
import datetime
import os
import hashlib
from hachoir_core.error import HachoirError
from hachoir_parser import createParser
from hachoir_metadata import extractMetadata, metadata_item

import constants
import httplib
import json


# Casts all values in a dictionary to a string
def serialize_dict(dictionary):
    if dictionary is None:
        raise Exception("Attempting to serialize None as a dictionary...")
    elif type(dictionary) is not dict:
        raise Exception("Attempting to serialize {} as a dictionary...".format(type(dictionary)))

    return_dict = {}
    for key in dictionary:
        value = dictionary[key]
        if type(value) is dict:
            return_dict[key] = serialize_dict(value)
        elif type(value) not in [str, unicode, int, float, bool]:
            return_dict[key] = unicode(value)
        else:
            return_dict[key] = dictionary[key]

    return return_dict


def print_dict(dict):
    print(json.dumps(dict, indent=4))


def _md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def fetch_attributes(blob_path):
    date_formatted = str(datetime.date.today())  # 2018-04-20
    date_epoch = time.time()  # epoch
    size = os.path.getsize(blob_path)  # in bytes
    split_name = os.path.basename(blob_path).split(".")
    name = split_name[0]  # "filename" from "filename.ext"
    extension = split_name[1]
    checksum = _md5(blob_path)


    # grab metadata from hachoir
    hachoir_metadata = _get_hachoir_metadata(blob_path)

    metadata = {
        "date": {
            "formatted": date_formatted,
            "epoch": date_epoch
        },
        "size": size,
        "name": name,
        "extension": extension,
        "extracted": hachoir_metadata,
        "unique_id": checksum
    }

    return metadata


def _get_hachoir_metadata(blob_path):
    parser = createParser(blob_path)
    if not parser:
        print "Unable to parse file"
        exit(1)
    try:
        metadata = extractMetadata(parser, quality=metadata_item.QUALITY_BEST)
    except HachoirError, err:
        print "Metadata extraction error: {}".format(err)
        metadata = None
    if not metadata:
        print "Unable to extract metadata"
        exit(1)

    transformed_metadata = {}

    exclude_fields = ["comment", "endian"]

    for data in metadata:
        key = data.key
        if len(data.values) is not 0 and key not in exclude_fields:
            value = data.values[0].value

            if type(value) is datetime.datetime:
                now = datetime.datetime.now()
                value = (now - datetime.datetime.fromtimestamp(0)).total_seconds()
            if type(value) is datetime.timedelta:
                value = value.total_seconds()

            transformed_metadata[key] = value

    return transformed_metadata


def validate_candidate(candidate, truth_dict):
    if type(candidate) is not dict:
        raise Exception("candidate must be of type dict")

    # make sure all the required keys are present and of correct type
    for key in truth_dict:
        if key not in candidate.keys():
            raise Exception("required key {} not found in candidate".format(key))

        value_type = type(candidate[key])
        required_value_types = truth_dict[key]
        if value_type not in required_value_types:
            raise Exception("candidate key {} is of type {} but has to be one of {}".format(key, value_type, required_value_types))

        if key is "date_uploaded":
            _validate_candidate_date(candidate[key])

        if key is "exposed_users":
            _validate_exposed_users(candidate[key])


def _validate_candidate_date(candidate):
    if not candidate.get("since_epoch"):
        raise Exception("date_uploaded must have following format: {since_epoch: <int>, formatted: <str>")

    # I got lazy, we can check the type of each key here too
    if not candidate.get("formatted"):
        raise Exception("date_uploaded must have following format: {since_epoch: <int>, formatted: <str>")


def _validate_exposed_users(candidate):
    for candidate_user in candidate:
        if type(candidate_user) is not dict:
            raise Exception("users must have keys {}, received {}".format(None, candidate_user))

        # if not candidate_user.get("key1"):
        #     raise Exception("asdfas")
        #
        # if not candidate_user.get("key2"):
        #     raise Exception("asdfasd")


def add_object(object_type, data, collection):
    error_message = None

    # validate desired object_type
    if object_type is None or object_type not in constants.OBJECT_TYPES:
        error_message = "object_type in /mongo/<object_type>/<ObjectId> must be one of {}".format(
            constants.OBJECT_TYPES)
        return error_message, httplib.BAD_REQUEST

    # validate candidate data
    try:
        document_data = data
        validate_candidate(document_data, constants.OBJECT_TYPES[object_type])
    except Exception as e:
        error_message = "Error accepting payload: {}".format(e)
        return error_message, httplib.BAD_REQUEST

    # add candidate to database
    try:
        document_id = collection.insert(document_data)
        document = collection.find_one({"_id": document_id})
    except Exception as e:
        error_message = "Error adding object to database: {}".format(e)
        return error_message, httplib.INTERNAL_SERVER_ERROR

    converted_doc = serialize_dict(document)
    converted_id = str(document_id)
    result = {converted_id: converted_doc}

    return result


def object_from_blob(blob_attributes):
    object_metadata = {
        "unique_id": blob_attributes["unique_id"],
        "date_uploaded": {
            "since_epoch": blob_attributes["date"]["epoch"],
            "formatted": blob_attributes["date"]["formatted"]
        },
        "file_size": blob_attributes["size"],
        "duration": blob_attributes["extracted"]["duration"],
        "file_location": blob_attributes["url_download"],
        "location": blob_attributes["url_location"],
        "ripe": False,
        "ripe_score": 0,
        "exposed_users": [],
        "blob_attributes": blob_attributes
    }

    return object_metadata


def get_filename(file_path):
    return os.path.basename(file_path)