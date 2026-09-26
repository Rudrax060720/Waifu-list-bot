from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# 📦 Collections
characters = db["characters"]
anime_col = db["anime"]
admins_col = db["admins"]


# ---------- Anime ----------
def normalize(anime):
    return anime.strip().lower()


def get_or_create_anime(anime):
    key = normalize(anime)

    data = anime_col.find_one({"name": key})
    if data:
        return data["anime_id"]

    last = anime_col.find_one(sort=[("anime_id", -1)])
    new_id = 1 if not last else last["anime_id"] + 1

    anime_col.insert_one({
        "anime_id": new_id,
        "name": key,
        "display": anime
    })

    return new_id


# ---------- Admin ----------
def is_admin(user_id: int) -> bool:
    return admins_col.find_one({"user_id": user_id}) is not None


def add_admin(user_id: int):
    admins_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )


def remove_admin(user_id: int):
    admins_col.delete_one({"user_id": user_id})


def get_all_admins():
    return list(admins_col.find({}, {"_id": 0}))


# ---------- Character Queries ----------
def get_characters_by_anime_and_type(anime: str, ctype: str):
    key = normalize(anime)
    return list(characters.find({
        "anime": key,
        "type": ctype
    }))


def get_available_anime():
    return list(anime_col.find({}, {"_id": 0, "display": 1}))
