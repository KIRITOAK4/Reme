import motor.motor_asyncio
from Krito import DB_URL, DB_NAME
from .utils import send_log

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
            uploadtype=None,
            metadata={
                "title": "t.me/devil_testing_bot",
                "artist": "t.me/devil_testing_bot",
                "audio": "t.me/devil_testing_bot",
                "author": "t.me/devil_testing_bot",
                "video": "t.me/devil_testing_bot",
                "subtitle": "t.me/devil_testing_bot"
            }
        )

    async def add_user(self, b, m):
        u = m.from_user
        chat_id = m.chat.id
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.col.insert_one(user)
            await send_log(b, u)

    async def is_user_exist(self, id):
        user = await self.col.find_one({"_id": int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id):
        await self.col.delete_many({"_id": int(user_id)})

    async def set_metadata(self, id, metadata):
        default_value = "t.me/devil_testing_bot"
        metadata_keys = ["title", "artist", "audio", "author", "video", "subtitle"]
        complete_metadata = {key: metadata.get(key, default_value) for key in metadata_keys}
        await self.col.update_one({"_id": int(id)}, {"$set": {"metadata": complete_metadata}})

    async def get_metadata(self, id):
        user = await self.db.users.find_one({"_id": int(id)})
        if user:
            metadata = user.get("metadata", {})
            default_value = "t.me/devil_testing_bot"
            metadata_keys = ["title", "artist", "audio", "author", "video", "subtitle"]
            for key in metadata_keys:
                metadata.setdefault(key, default_value)
            return metadata
        return None

    async def set_thumbnail(self, id, file_id):
        await self.col.update_one({"_id": int(id)}, {"$set": {"file_id": file_id}})

    async def get_thumbnail(self, id):
        user = await self.db.users.find_one({"_id": int(id)})
        if user:
            return user.get("file_id", None)
        return None

    async def set_caption(self, id, caption):
        await self.col.update_one({"_id": int(id)}, {"$set": {"caption": caption}})

    async def get_caption(self, id):
        user = await self.db.users.find_one({"_id": int(id)})
        if user:
            return user.get("caption", None)
        return None

    async def set_template(self, id, template):
        await self.col.update_one({"_id": int(id)}, {"$set": {"template": template}})

    async def get_template(self, id):
        user = await self.db.users.find_one({"_id": int(id)})
        if user:
            return user.get("template", None)
        return None

    async def set_uploadtype(self, id, uploadtype):
        await self.col.update_one({"_id": int(id)}, {"$set": {"uploadtype": uploadtype}})

    async def get_uploadtype(self, id):
        user = await self.db.users.find_one({"_id": int(id)})
        if user:
            return user.get("uploadtype", None)
        return None

    async def set_exten(self, id, exten):
        await self.col.update_one({"_id": int(id)}, {"$set": {"exten": exten}})

    async def get_exten(self, id):
        user = await self.db.users.find_one({"_id": int(id)})
        if user:
            return user.get("exten", None)
        return None

    async def set_token(self, id, token):
        await self.col.update_one(
            {"_id": int(id)},
            {"$set": {"token": token}}
        )

    async def set_time(self, id, time):
        await self.col.update_one(
            {"_id": int(id)},
            {"$set": {"time": time}}
        )

    async def get_token_and_time(self, id):
        user = await self.db.users.find_one({"_id": int(id)})
        if user:
            return user.get("token", None), user.get("time", None)
            return None, None
        
    async def remove_time_field(self, id):
        await self.col.update_one({"_id": int(id)}, {"$unset": {"time": ""}})

    async def set_space_used(self, id, space_used):
        """
        Set the amount of space used by a user.
        :param id: User ID
        :param space_used: Space used in bytes
        """
        await self.col.update_one(
            {"_id": int(id)},
            {"$set": {"space_used": space_used}}
        )

    async def get_space_used(self, id):
        """
        Get the amount of space used by a user.
        :param id: User ID
        :return: Space used in bytes (default: 0)
        """
        user = await self.col.find_one({"_id": int(id)})
        if user:
            return user.get("space_used", 0)  # Default to 0 if not set
        return 0

    async def set_sample_value(self, id, value):
        """
        Set the sample button value for a user.
        :param id: User ID
        :param value: New sample value
        """
        await self.col.update_one(
            {"_id": int(id)},
            {"$set": {"sample_value": value}}
        )

    async def get_sample_value(self, id):
        """
        Get the sample button value for a user.
        :param id: User ID
        :return: Sample value (default: 0)
        """
        user = await self.col.find_one({"_id": int(id)})
        if user:
            return user.get("sample_value", 0)  # Default to 0 if not set
        return 0

    async def update_metadata_for_old_users(self):
        update_fields = {
            "chat_id": None,
            "file_id": None,
            "caption": None,
            "token": None,
            "time": None,
            "exten": None,
            "template": None,
            "sample_value": 0,
            "space_used": 0,
            "uploadtype": None,
            "metadata": {
                "title": "t.me/devil_testing_bot",
                "artist": "t.me/devil_testing_bot",
                "audio": "t.me/devil_testing_bot",
                "author": "t.me/devil_testing_bot",
                "video": "t.me/devil_testing_bot",
                "subtitle": "t.me/devil_testing_bot"
            }
        }

        async for user in self.col.find({}):
            user_id = user["_id"]
            updated_data = {key: user.get(key, value) for key, value in update_fields.items()}
            if "metadata" in user:
                updated_metadata = {key: user["metadata"].get(key, value) for key, value in update_fields["metadata"].items()}
            else:
                updated_metadata = update_fields["metadata"]
            updated_data["metadata"] = updated_metadata
            await self.col.update_one({"_id": user_id}, {"$set": updated_data})
        

db = Database(DB_URL, DB_NAME)
