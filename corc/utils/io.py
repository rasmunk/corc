import os
import fcntl
import yaml
import shutil


def copy(src, dst):
    try:
        shutil.copy(src, dst)
        return True
    except Exception as err:
        print("Failed to copy file: {} - {}".format(src, err))
    return False


def makedirs(path):
    try:
        os.makedirs(path)
        return True
    except Exception as err:
        print("Failed to create directory path: {} - {}".format(path, err))
    return False


def acquire_lock(path, mode=fcntl.LOCK_EX):
    lock = open(path, "w+")
    try:
        fcntl.flock(lock.fileno(), mode)
        return lock
    except IOError as ioerr:
        print("Failed to acquire lock: {} - {}".format(path, ioerr))
        # Clean up
        try:
            lock.close()
        except Exception as err:
            print("Failed to close lock after failling to acquire it: {}".format(err))
    return None


def release_lock(lock, close=True):
    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    if close:
        try:
            lock.close()
        except Exception as err:
            print("Failed to close file during lock release: {} - {}".format(lock, err))


def write(path, content, mode="w", mkdirs=False):
    dir_path = os.path.dirname(path)
    if not exists(dir_path) and mkdirs:
        if not makedirs(dir_path):
            return False
    try:
        with open(path, mode) as fh:
            fh.write(content)
        return True
    except Exception as err:
        print("Failed to save file: {} - {}".format(path, err))
    return False


def load(path, mode="r", readlines=False):
    try:
        with open(path, mode) as fh:
            if readlines:
                return fh.readlines()
            return fh.read()
    except Exception as err:
        print("Failed to load file: {} - {}".format(path, err))
    return False


def join(path, *paths):
    return os.path.join(path, *paths)


def remove(path):
    try:
        if exists(path):
            os.remove(path)
            return True
    except Exception as err:
        print("Failed to remove file: {} - {}".format(path, err))
    return False


def removedirs(path, recursive=False):
    try:
        if exists(path):
            if recursive:
                shutil.rmtree(path)
            else:
                os.removedirs(path)
            return True
    except Exception as err:
        print("Failed to remove directory: {} - {}".format(path, err))
    return False


def remove_content_from_file(path, content):
    if not exists(path):
        return False

    if not content:
        return False

    lines = []
    with open(path, "r") as rh:
        lines = rh.readlines()

    with open(path, "w") as wh:
        for current_line in lines:
            if content not in current_line:
                wh.write(current_line)


def exists(path):
    if not path:
        return False
    if not isinstance(path, str):
        return False
    return os.path.exists(path)


def chmod(path, mode, **kwargs):
    try:
        os.chmod(path, mode, **kwargs)
    except Exception as err:
        print("Failed to set permissions: {} on: {} - {}".format(mode, path, err))
        return False
    return True


def parse_yaml(data):
    try:
        parsed = yaml.safe_load(data)
        return parsed
    except yaml.reader.ReaderError as err:
        print("Failed to parse yaml: {}".format(err))
    return False


def dump_yaml(path, data):
    try:
        with open(path, "w") as fh:
            yaml.dump(data, fh)
        return True
    except IOError as err:
        print("Failed to dump yaml: {} - {}".format(path, err))
    return False


def load_yaml(path):
    try:
        with open(path, "r") as fh:
            return yaml.safe_load(fh)
    except IOError as err:
        print("Failed to load yaml: {} - {}".format(path, err))
    return False
