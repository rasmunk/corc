# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import shelve
import os
import uuid
from dbm import whichdb, _names
from corc.core.defaults import default_persistence_path
from corc.core.persistence import (
    create_persistence_directory,
    persistence_directory_exists,
)
from corc.utils.io import acquire_lock, release_lock, remove
from corc.utils.io import exists as path_exists

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
            return {item[0]: item[1] for item in db.items()}

    async def values(self):
        with shelve.open(self._shelve_path) as db:
            return list(db.values())

    async def keys(self):
        with shelve.open(self._shelve_path) as db:
            return list(db.keys())

    async def add(self, value, key=None):
        _id = key
        if not key:
            _id = str(uuid.uuid4())

        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            with shelve.open(self._shelve_path) as db:
                db[_id] = value
        except Exception:
            return False
        finally:
            release_lock(lock)
        return _id

    async def remove(self, key):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            with shelve.open(self._shelve_path) as db:
                db.pop(key)
        except Exception:
            return False
        finally:
            release_lock(lock)
        return True

    async def update(self, key, value):
        lock = acquire_lock(self._lock_path)
        if not lock:
            return False
        try:
            with shelve.open(self._shelve_path) as db:
                db[key] = value
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
            if path_exists(database_path) and not remove(database_path):
                return False
            if path_exists(self._lock_path) and not remove(self._lock_path):
                return False
        except Exception:
            return False
        finally:
            release_lock(lock)
        return True

    async def get(self, key):
        with shelve.open(self._shelve_path) as db:
            return db.get(key)

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
                [db.pop(key) for key in db.keys()]
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
        return path_exists(self.get_database_path())

    def _find_database_path(self):
        database_module_type = discover_database_module_type(self._shelve_path)
        database_possible_postfixes = get_database_possible_postfixes(
            database_module_type
        )
        for postfix in database_possible_postfixes:
            possible_path = self._shelve_path + postfix
            if path_exists(possible_path):
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
async def discover_databases(directory_path, database_prefix=None):
    if not path_exists(directory_path):
        return []

    databases = []
    for _file in os.listdir(directory_path):
        if _file.endswith(DATABASE_LOCK_FILE_POSTFIX):
            continue

        if not database_prefix:
            databases.append(_file)
        else:
            if _file.startswith(database_prefix):
                databases.append(_file)
    return databases
