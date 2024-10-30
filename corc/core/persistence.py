from corc.core.defaults import default_persistence_path
from corc.utils.io import makedirs, exists, removedirs


def create_persistence_directory(path=default_persistence_path):
    if not exists(path):
        return makedirs(path)
    return True


def persistence_directory_exists(path=default_persistence_path):
    return exists(path)


def remove_persistence_directory(path=default_persistence_path):
    if not exists(path):
        return True
    return removedirs(path)
