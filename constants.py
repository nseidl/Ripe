import os

SERVER_DEFAULTS = {
    "HOST": os.getenv("HOST", "127.0.0.1"),
    "PORT": int(os.getenv("PORT", 8000)),
}

MONGO_DEFAULTS = {
    "MONGO_URL": os.getenv("MONGODB_URI"),
    "COLLECTION_NAME": os.getenv("MONGO_COLLECTION_NAME", "heroku_7wmzjn5f")
}

S3_DEFAULTS = {
    "BUCKET_NAME": os.getenv("S3_BUCKET_NAME"),
    "ACCESS_KEY": os.getenv("AWS_ACCESS_KEY_ID"),
    "SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY")
}

SERVER_ENDPOINTS = {
    "GET_OBJ":      "/mongo/<object_type>/<object_id>",
    "POST_OBJ":     "/mongo/<object_type>/",
    "POST_BLOB":    "/mongo/blobs/",
    "GET_BLOB":     "/mongo/blobs/<blob_id>"
}

VIDEO_FORMAT = {
    "unique_id": [str, unicode],
    "date_uploaded": [dict],
    "file_size": [int],
    "duration": [int, float],
    "file_location": [str, unicode],
    "location": [str, unicode],
    "ripe": [bool],
    "ripe_score": [int, float],
    "exposed_users": [list],
}

USER_FORMAT = {
    "unique_id": [str, unicode],
    "date_created": [dict],
    "username": [str, unicode],
    "password_hash": [str, unicode],
    "name_first": [str, unicode],
    "name_last": [str, unicode],
    "dob": [str, unicode],
    "gender": [str, unicode],
    "exposed_videos": [list],
    "location": [str, unicode],
    "current_peaches": [list],
    "all_peaches": [list],

}

OBJECT_TYPES = {
    "users": USER_FORMAT,
    "media": VIDEO_FORMAT,
    "blobs": None
}

_min = 60
_hr = 60 * _min
_day = 24 * _hr
_year = 365 * _day
BLOB_EXPIRATION = 1 * _year
