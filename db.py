from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

characters = db["characters"]
anime_col = db["anime"]

def normalize(anime):
    return anime.strip().lower()

def get_or_create_anime(anime):
    key = normalize(anime)

    data = anime_col.find_one({"name": key})

    if data:
        return data["anime_id"]

    # create new anime with auto ID
    last = anime_col.find_one(sort=[("anime_id", -1)])

    new_id = 1 if not last else last["anime_id"] + 1

    anime_col.insert_one({
        "anime_id": new_id,
        "name": key,
        "display": anime
    })

    return new_id
