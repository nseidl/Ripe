"""
TODO:
- Change to Python logging module
- Improve example media and user JSON
- Improve add blob script
- Improve endpoint documentation
"""

import constants
import utils

from flask import Flask, request
from flask_restful import Resource, Api
from flask_pymongo import PyMongo, wrappers, ObjectId
import os
import boto3
import httplib


"""SETUP APP"""
HOST = constants.SERVER_DEFAULTS["HOST"]
PORT = constants.SERVER_DEFAULTS["PORT"]
MONGO_URL = constants.MONGO_DEFAULTS["MONGO_URL"]
SETTINGS = {
    "host": HOST,
    "port": PORT,
    "debug": False
}

app = Flask(__name__)
app.config["MONGO_URI"] = MONGO_URL


"""SETUP MONGO"""
mongo = PyMongo(app)
mongo_client = wrappers.MongoClient(MONGO_URL)
MONGO_COLLECTION = mongo_client[constants.MONGO_DEFAULTS["COLLECTION_NAME"]]
MONGO_USERS = MONGO_COLLECTION["ripe-users"]
MONGO_MEDIA = MONGO_COLLECTION["ripe-media"]


"""SETUP API"""
api = Api(app)


"""SETUP S3"""
S3_BUCKET = constants.S3_DEFAULTS["BUCKET_NAME"]
AWS_ACCESS_KEY_ID = constants.S3_DEFAULTS["ACCESS_KEY"]
AWS_SECRET_ACCESS_KEY = constants.S3_DEFAULTS["SECRET_ACCESS_KEY"]


# utility endpoint to GET and POST Mongo objects
class MongoGeneral(Resource):
    @staticmethod
    def get(object_type=None, object_id=None):
        error_message = None

        # validate desired object_type
        if object_type is None or object_type not in constants.OBJECT_TYPES:
            error_message = "object_type in /mongo/<object_type>/<ObjectId> must be one of {}".format(constants.OBJECT_TYPES.keys())
            return error_message, httplib.BAD_REQUEST

        # determine whether to return desired object or all objects
        get_all = False if object_id else True

        # try to get data
        result = None
        try:
            collection = MONGO_COLLECTION["ripe-" + object_type]
            if get_all:
                result = {}
                for doc in collection.find():
                    converted_doc = utils.serialize_dict(doc)
                    doc_id = converted_doc["_id"]
                    result[doc_id] = converted_doc
            else:
                item = utils.serialize_dict(collection.find_one({"_id": ObjectId(object_id)}))
                result = item
        except Exception as e:
            error_message = "Error finding ObjectId={}; {}".format(object_id, e)
            return error_message, httplib.BAD_REQUEST

        return result, httplib.CREATED

    # post the given json blob
    # see README to format POST request
    @staticmethod
    def post(object_type=None):
        result = utils.add_object(object_type, request, MONGO_COLLECTION["ripe-" + object_type])
        print(result)

        print "object_id={} successfully added".format(result.keys()[0])

        return result, httplib.CREATED


# utility endpoint for GET and POST blobs
class MongoUploadBlob(Resource):
    def post(self):
        error_message = None

        blob_name = request.args.get("blob_name")
        if blob_name is None:
            error_message = "blob_name must be provided as request arguments"
            return error_message, httplib.BAD_REQUEST

        # save blob to /tmp/<blob_name>
        blob = request.files["blob"]
        blob_path = os.path.join("/tmp/", blob_name)
        blob.save(blob_path)

        # fetch attributes from media blob
        blob_attributes = utils.fetch_attributes(blob_path)

        # upload blob to ripe-staging bucket
        try:
            s3_client = boto3.client("s3",
                                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
            print("posting blob to s3...")
            s3_client.upload_file(blob_path, S3_BUCKET, utils.get_filename(blob_path))
            print("done posting blob to s3")
        except Exception as e:
            error_message = str(e)
            return error_message, httplib.INTERNAL_SERVER_ERROR

        # remove file so we don't waste local space
        os.remove(blob_path)

        # generate a download link
        download_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": blob_name,
            },
            ExpiresIn=constants.BLOB_EXPIRATION
        )

        blob_location = "https://{}.s3.amazonaws.com/{}".format(S3_BUCKET, blob_name)

        blob_attributes["url_download"] = download_url
        blob_attributes["url_location"] = blob_location

        object_attributes = utils.object_from_blob(blob_attributes)

        # post the attributes
        object_attributes = utils.add_object("media", object_attributes, MONGO_COLLECTION["ripe-media"])

        result = {
            "blob_attributes": blob_attributes,
            "object_attributes": object_attributes,
        }

        print(result)

        return result, httplib.CREATED


# utility endpoint to GET simple general information
class GeneralInformation(Resource):
    def get(self):
        write_dict = {
            # "MONGO_URL": MONGO_URL,
            "Message of the day": "Welcome to Ripe.",
            "sample_user": self._get_random_doc(MONGO_USERS),
            "sample_media": self._get_random_doc(MONGO_MEDIA)
        }

        return write_dict

    @staticmethod
    def _get_random_doc(collection):
        random_pipeline = [{"$sample": {
            "size": 1}
        }]
        random_cursor = {"batchSize": 1}
        sample_document = collection.aggregate(pipeline=random_pipeline, cursor=random_cursor)
        sample_document = sample_document.next()
        sample_document = utils.serialize_dict(sample_document)
        return sample_document


# utility endpoint to GET simple general information pertaining to MongoDB
class MongoInfo(Resource):

    # simply produces all objects
    @staticmethod
    def get():
        all_docs = {}
        data_sets = [MONGO_USERS, MONGO_MEDIA]

        for data_set in data_sets:
            for doc in data_set.find():
                converted_doc = utils.serialize_dict(doc)
                doc_id = converted_doc["_id"]
                all_docs[doc_id] = converted_doc

        if len(all_docs.keys()) is 0:
            return "no objects"

        return all_docs


"""ADD ENDPOINTS"""
# add informational endpoints
api.add_resource(GeneralInformation, "/")
api.add_resource(MongoInfo, "/mongo/")

# add general object endpoint
api.add_resource(MongoGeneral, constants.SERVER_ENDPOINTS["GET_OBJ"],
                                constants.SERVER_ENDPOINTS["POST_OBJ"])

# add blob upload endpoint
api.add_resource(MongoUploadBlob, constants.SERVER_ENDPOINTS["POST_BLOB"],
                                    constants.SERVER_ENDPOINTS["GET_BLOB"])
if __name__ == "__main__":
    app.run(**SETTINGS)

# helpful: https://spapas.github.io/2014/06/30/rest-flask-mongodb-heroku/
