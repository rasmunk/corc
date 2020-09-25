import paramiko
import os
from io import StringIO
from corc.io import write, chmod, acquire_lock, release_lock, remove_content_from_file
from corc.io import load as fileload
from corc.io import remove as fileremove
from corc.helpers import get_corc_path
from corc.defaults import default_base_path, default_host_key_order


default_ssh_path = os.path.join(default_base_path, "ssh")


def gen_rsa_ssh_key_pair(size=2048):
    rsa_key = paramiko.RSAKey.generate(size)
    string_io_obj = StringIO()
    rsa_key.write_private_key(string_io_obj)

    private_key = string_io_obj.getvalue()
    public_key = ("ssh-rsa %s" % (rsa_key.get_base64())).strip()
    return private_key, public_key


def gen_ssh_credentials(ssh_dir_path=default_ssh_path, key_name="id_rsa", size=2048):
    private_key, public_key = gen_rsa_ssh_key_pair(size=size)
    corc_ssh_path = get_corc_path(path=ssh_dir_path, env_postfix="SSH_PATH")
    credentials = SSHCredentials(
        private_key=private_key,
        private_key_file=os.path.join(corc_ssh_path, key_name),
        public_key=public_key,
        public_key_file=os.path.join(corc_ssh_path, "{}.pub".format(key_name)),
    )
    return credentials


class SSHCredentials:
    def __init__(
        self,
        user=None,
        password=None,
        private_key=None,
        private_key_file=None,
        public_key=None,
        public_key_file=None,
        store_keys=False,
    ):
        self._user = user
        self._password = password
        self._private_key = private_key
        self._private_key_file = private_key_file
        self._public_key = public_key
        self._public_key_file = public_key_file
        if store_keys:
            self.save()

    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password

    @property
    def private_key(self):
        return self._private_key

    @property
    def private_key_file(self):
        return self._private_key_file

    @property
    def public_key(self):
        return self._public_key

    @property
    def public_key_file(self):
        return self._public_key_file

    def store(self):
        if write(self.private_key_file, self.private_key, mkdirs=True) and write(
            self.public_key_file, self.public_key, mkdirs=True
        ):
            # Ensure the correct permissions
            if chmod(self.private_key_file, 0o600) and chmod(
                self.public_key_file, 0o644
            ):
                return True
        return False

    def load(self):
        if self.private_key_file:
            self.private_key = fileload(self.private_key_file)
        if self.public_key_file:
            self.public_key = fileload(self.public_key_file)

    def remove(self):
        if os.path.exists(self.private_key_file):
            if not fileremove(self.private_key_file):
                return False
        if os.path.exists(self.public_key_file):
            if not fileremove(self.public_key_file):
                return False
        return True


class SSHAuthenticator:
    # TODO, make independent known_hosts file path inside the corc directory

    def __init__(self, credentials=None):
        if not credentials:
            self._credentials = gen_ssh_credentials()
        else:
            self._credentials = credentials

    @property
    def credentials(self):
        return self._credentials

    def get_host_key(
        self, endpoint, port=22, default_host_key_algos=default_host_key_order,
    ):
        transport = paramiko.transport.Transport("{}:{}".format(endpoint, port))
        transport.start_client()
        # Ensure that we use the same HostKeyAlgorithm order across
        # SSH implementations
        transport.get_security_options().key_types = tuple(default_host_key_algos)
        host_key = transport.get_remote_server_key()
        return host_key

    def prepare(self, endpoint):
        # Get the host key of the target endpoint
        host_key = self.get_host_key(endpoint)
        return self.add_to_known_hosts(endpoint, host_key)

    def cleanup(self, endpoint):
        credentials_removed = self.remove_credentials()
        known_host_removed = self.remove_from_known_hosts(endpoint)
        return credentials_removed and known_host_removed

    def add_to_known_hosts(self, endpoint, host_key):
        path = os.path.join(os.path.expanduser("~"), ".ssh", "known_hosts")
        lock_path = "{}_lock".format(path)
        known_host_str = "{endpoint} {key_type} {host_key}\n".format(
            endpoint=endpoint,
            key_type=host_key.get_name(),
            host_key=host_key.get_base64(),
        )
        known_hosts_lock = acquire_lock(lock_path)
        if write(path, known_host_str, mode="+a"):
            release_lock(known_hosts_lock)
            return True
        release_lock(known_hosts_lock)
        return False

    def remove_from_known_hosts(self, endpoint):
        # TODO, make independent known_hosts file path inside the corc directory
        path = os.path.join(os.path.expanduser("~"), ".ssh", "known_hosts")
        lock_path = "{}_lock".format(path)
        known_hosts_lock = acquire_lock(lock_path)
        remove_content_from_file(path, endpoint)
        release_lock(known_hosts_lock)
        return True

    def store_credentials(self):
        return self.credentials.store()

    def remove_credentials(self):
        return self.credentials.remove()
