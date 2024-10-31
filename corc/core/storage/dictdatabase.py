import shelve
import os
from dbm import whichdb, _names
from corc.core.defaults import default_persistence_path
from corc.core.persistence import (
    create_persistence_directory,
    persistence_directory_exists,
)
from corc.utils.io import acquire_lock, release_lock, remove
from corc.utils.io import exists as file_exists

# We extract from the underlying dbm module
# which possible database types would be used to
# manage the underlying shelve
# The selection is based on which of the _names modules is
# installed on the system
DATABASE_TYPES = _names

DATABASE_LOCK_FILE_POSTFIX = "lock"


class DictDatabase:
    def __init__(self, name, directory=None):
        """
        :param name: The name of the database
        :param directory: The directory where the database should be stored.
        If not provided, the default_persistence_path will be used.
        """

        self.name = name
        if not directory:
            directory = default_persistence_path
        self.directory = directory
        if not persistence_directory_exists(self.directory):
            if not create_persistence_directory(self.directory):
                raise IOError(
                    "Failed to create persistence directory: {}".format(self.directory)
                )

        self._shelve_path = os.path.join(self.directory, self.name)
        self._lock_path = "{}.{}".format(self._shelve_path, DATABASE_LOCK_FILE_POSTFIX)

    def get_database_path(self):
        return self._find_database_path()

    def asdict(self):
        return {
            "name": self.name,
            "database_path": self.get_database_path(),
            "lock_path": self._lock_path,
        }

    async def is_empty(self):
        with shelve.open(self._shelve_path) as db:
            return len(db) == 0

    async def items(self):
        with shelve.open(self._shelve_path) as db:
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
            with shelve.open(self._shelve_path) as db:
                db[_id] = item
        except Exception:
            return False
        finally:
            release_lock(lock)
        return True

    async def remove(self, item_id):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            with shelve.open(self._shelve_path) as db:
                db.pop(item_id)
        except Exception:
            return False
        finally:
            release_lock(lock)
        return True

    async def update(self, item_id, item):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            with shelve.open(self._shelve_path) as db:
                db[item_id] = item
        except Exception:
            return False
        finally:
            release_lock(lock)
        return True

    async def remove_persistence(self):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            database_path = self.get_database_path()
            if file_exists(database_path) and not remove(database_path):
                return False
            if file_exists(self._lock_path) and not remove(self._lock_path):
                return False
        except Exception:
            return False
        finally:
            release_lock(lock)
        return True

    async def get(self, item_id):
        with shelve.open(self._shelve_path) as db:
            return db.get(item_id)

    async def find(self, key, value):
        with shelve.open(self._shelve_path) as db:
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
            with shelve.open(self._shelve_path) as db:
                [db.pop(item_id) for item_id in db.keys()]
        except Exception:
            return False
        finally:
            release_lock(lock)
        return True

    async def touch(self):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False

        try:
            with shelve.open(self._shelve_path) as _:
                pass
        except Exception:
            return False
        finally:
            release_lock(lock)
        return True

    async def exists(self):
        return file_exists(self.get_database_path())

    def _find_database_path(self):
        database_module_type = discover_database_module_type(self._shelve_path)
        database_possible_postfixes = get_database_possible_postfixes(
            database_module_type
        )
        for postfix in database_possible_postfixes:
            possible_path = self._shelve_path + postfix
            if file_exists(possible_path):
                return possible_path
        return False


def discover_database_module_type(path):
    return whichdb(path)


def get_database_possible_postfixes(database_type):
    if database_type == "dbm.ndbm":
        return [".pag", ".dir", ".db"]
    if database_type == "dbm.dumb":
        return [".dat", ".dir"]
    return [""]


# Note, simple discover method that has be to be improved.
# Might create a designed path where the pools are stored
async def discover_databases(directory_path):
    databases = []
    for file in os.listdir(directory_path):
        if not file.endswith(DATABASE_LOCK_FILE_POSTFIX):
            databases.append(file)
    return databases
