import motor.motor_asyncio
from Krito import DB_URL, DB_NAME
from .utils import send_log
from pytz import timezone

IST = timezone("Asia/Kolkata")

DEFAULT_METADATA = {
    "title": "t.me/devil_testing_bot",
    "artist": "t.me/devil_testing_bot",
    "audio": "t.me/devil_testing_bot",
    "author": "t.me/devil_testing_bot",
    "video": "t.me/devil_testing_bot",
    "subtitle": "t.me/devil_testing_bot"
}

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id):
        return dict(
            _id=int(id),
            chat_id=None,
            file_id=None,
            caption=None,
            token=None,
            time=None,
            exten=None,
            template=None,
            sample_value=0,
            space_used=0,
            filled_at=None,
            uploadtype=None,
            metadata=DEFAULT_METADATA.copy()
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            await self.col.insert_one(self.new_user(u.id))
            await send_log(b, u)

    async def is_user_exist(self, id):
        return bool(await self.col.find_one({"_id": int(id)}))

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"_id": int(user_id)})

    async def set_metadata(self, id, metadata):
        metadata = {key: metadata.get(key, DEFAULT_METADATA[key]) for key in DEFAULT_METADATA}
        await self.col.update_one({"_id": int(id)}, {"$set": {"metadata": metadata}})

    async def get_metadata(self, id):
        user = await self.col.find_one({"_id": int(id)})
        if user:
            metadata = user.get("metadata", {})
            return {key: metadata.get(key, DEFAULT_METADATA[key]) for key in DEFAULT_METADATA}
        return None

    async def set_thumbnail(self, id, file_id):
        await self.col.update_one({"_id": int(id)}, {"$set": {"file_id": file_id}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return user.get("file_id") if user else None

    async def set_caption(self, id, caption):
        await self.col.update_one({"_id": int(id)}, {"$set": {"caption": caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return user.get("caption") if user else None

    async def set_template(self, id, template):
        await self.col.update_one({"_id": int(id)}, {"$set": {"template": template}})

    async def get_template(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return user.get("template") if user else None

    async def set_uploadtype(self, id, uploadtype):
        await self.col.update_one({"_id": int(id)}, {"$set": {"uploadtype": uploadtype}})

    async def get_uploadtype(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return user.get("uploadtype") if user else None

    async def set_exten(self, id, exten):
        await self.col.update_one({"_id": int(id)}, {"$set": {"exten": exten}})

    async def get_exten(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return user.get("exten") if user else None

    async def set_token(self, id, token):
        await self.col.update_one({"_id": int(id)}, {"$set": {"token": token}})

    async def set_time(self, id, time):
        await self.col.update_one({"_id": int(id)}, {"$set": {"time": time}})

    async def get_token_and_time(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return (user.get("token"), user.get("time")) if user else (None, None)

    async def remove_time_field(self, id):
        await self.col.update_one({"_id": int(id)}, {"$unset": {"time": ""}})

    async def set_space_used(self, id, space_used):
        await self.col.update_one({"_id": int(id)}, {"$set": {"space_used": space_used}})

    async def get_space_used(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return user.get("space_used", 0) if user else 0

    async def set_filled_time(self, user_id, timestamp):
        await self.col.update_one({"_id": user_id}, {"$set": {"filled_at": timestamp}}, upsert=True)

    async def get_filled_time(self, user_id):
        user = await self.col.find_one({"_id": user_id})
        return user.get("filled_at") if user else None

    async def reset_filled_time(self, user_id):
        await self.col.update_one({"_id": user_id}, {"$unset": {"filled_at": ""}})

    async def set_sample_value(self, id, value):
        await self.col.update_one({"_id": int(id)}, {"$set": {"sample_value": value}})

    async def get_sample_value(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return user.get("sample_value", 0) if user else 0

db = Database(DB_URL, DB_NAME)
