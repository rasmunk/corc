import shelve
import os
from corc.utils.io import acquire_lock, release_lock, remove
from corc.utils.io import exists as file_exists


class DictDatabase:
    def __init__(self, name):
        self.name = name
        self._database_path = "{}.db".format(self.name)
        self._lock_path = "{}.lock".format(self.name)

    def asdict(self):
        return {
            "name": self.name,
            "database_path": self._database_path,
            "lock_path": self._lock_path,
        }

    async def is_empty(self):
        with shelve.open(self._database_path) as db:
            return len(db) == 0

    async def items(self):
        with shelve.open(self._database_path) as db:
            return [item for item in db.values()]

    async def add(self, item):
        _id = None
        if hasattr(item, "id"):
            _id = item.id
        elif "id" in item:
            _id = item["id"]
        else:
            raise AttributeError(
                "add item must have an id attribute or a key named id."
            )

        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            with shelve.open(self._database_path) as db:
                db[_id] = item
        except Exception as err:
            print(err)
            return False
        finally:
            release_lock(lock)
        return True

    async def remove(self, item_id):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            with shelve.open(self._database_path) as db:
                db.pop(item_id)
        except Exception as err:
            print(err)
            return False
        finally:
            release_lock(lock)
        return True

    async def update(self, item_id, item):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            with shelve.open(self._database_path) as db:
                db[item_id] = item
        except Exception as err:
            print(err)
            return False
        finally:
            release_lock(lock)
        return True

    async def remove_persistence(self):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            if not remove(self._database_path):
                return False
            if not remove(self._lock_path):
                return False
        except Exception as err:
            print(err)
            return False
        finally:
            release_lock(lock)
        return True

    async def get(self, item_id):
        with shelve.open(self._database_path) as db:
            return db.get(item_id)

    async def find(self, key, value):
        with shelve.open(self._database_path) as db:
            return [
                item
                for item in db.values()
                if hasattr(item, key) and getattr(item, key) == value
            ]

    async def flush(self):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False

        try:
            with shelve.open(self._database_path) as db:
                [db.pop(item_id) for item_id in db.keys()]
        except Exception as err:
            print(err)
            return False
        finally:
            release_lock(lock)
        return True

    async def touch(self):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False

        try:
            with shelve.open(self._database_path) as _:
                pass
        except Exception as err:
            print(err)
            return False
        finally:
            release_lock(lock)
        return True

    async def exists(self):
        return file_exists(self._database_path)


# Note, simple discover method that has be to be improved.
# Might create a designed path where the pools are stored
async def discover_dict_db(path):
    pools = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".db"):
                pools.append(file.replace(".db", ""))
    return pools
