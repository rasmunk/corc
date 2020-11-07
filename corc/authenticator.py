import paramiko
import os
import subprocess
from io import StringIO
from corc.io import write, chmod, acquire_lock, release_lock, remove_content_from_file
from corc.io import load as fileload
from corc.io import remove as fileremove
from corc.helpers import get_corc_path
from corc.defaults import default_base_path, default_host_key_order


default_ssh_path = os.path.join(default_base_path, "ssh")


def make_certificate(identity, private_key_path, public_key_path):
    result = subprocess.run(
        ["ssh-keygen", "-s", private_key_path, "-I", identity, public_key_path],
        capture_output=True,
    )

    if hasattr(result, "returncode"):
        return_code = getattr(result, "returncode")
        if return_code == 0:
            return True
    return False


def gen_rsa_ssh_key_pair(size=2048):
    rsa_key = paramiko.RSAKey.generate(size)
    string_io_obj = StringIO()
    rsa_key.write_private_key(string_io_obj)

    private_key = string_io_obj.getvalue()
    public_key = ("ssh-rsa %s" % (rsa_key.get_base64())).strip()
    return private_key, public_key


def gen_ssh_credentials(
    ssh_dir_path=default_ssh_path,
    key_name="id_rsa",
    size=2048,
    create_certificate=False,
    certificate_kwargs=None,
):
    if not certificate_kwargs:
        certificate_kwargs = {}

    private_key, public_key = gen_rsa_ssh_key_pair(size=size)
    corc_ssh_path = get_corc_path(path=ssh_dir_path, env_postfix="SSH_PATH")

    private_key_file = os.path.join(corc_ssh_path, key_name)
    public_key_file = os.path.join(corc_ssh_path, "{}.pub".format(key_name))

    credential_kwargs = dict(
        private_key=private_key,
        private_key_file=private_key_file,
        public_key=public_key,
        public_key_file=public_key_file,
    )

    credentials = SSHCredentials(**credential_kwargs)

    # For now the make_certificate function requires that the credentials exists
    # in the FS
    if create_certificate:
        credentials.store()
        if "identity" not in certificate_kwargs:
            certificate_kwargs["identity"] = "UserIdentity"
        certificate_file = os.path.join(corc_ssh_path, "{}-cert.pub".format(key_name))
        if make_certificate(
            certificate_kwargs["identity"], private_key_file, public_key_file
        ):
            credential_kwargs["certificate_file"] = certificate_file
            credential_kwargs["certificate"] = fileload(certificate_file)
        else:
            print("Failed to create certificate file: {}".format(certificate_file))
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
        certificate=None,
        certificate_file=None,
        store_credentials=False,
    ):
        self._user = user
        self._password = password
        self._private_key = private_key
        self._private_key_file = private_key_file
        self._public_key = public_key
        self._public_key_file = public_key_file
        self._certificate = certificate
        self._certificate_file = certificate_file
        if store_credentials:
            self.store()

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

    @property
    def certificate(self):
        return self._certificate

    @property
    def certificate_file(self):
        return self._certificate_file

    def store(self):
        if self.private_key_file and self.private_key:
            if not write(
                self.private_key_file, self.private_key, mkdirs=True
            ) or not chmod(self.private_key_file, 0o600):
                return False

        if self.public_key_file and self.public_key:
            if not write(
                self.public_key_file, self.public_key, mkdirs=True
            ) or not chmod(self.public_key_file, 0o644):
                return False

        if self.certificate_file and self.certificate:
            if not write(
                self.certificate_file, self.certificate, mkdirs=True
            ) or not chmod(self.certificate_file, 0o644):
                return False
        return True

    def load(self):
        if self.private_key_file:
            self.private_key = fileload(self.private_key_file)
        if self.public_key_file:
            self.public_key = fileload(self.public_key_file)
        if self.certificate_file:
            self.certificate_file = fileload(self.certificate_file)

    def remove(self):
        if self.private_key_file and os.path.exists(self.private_key_file):
            if not fileremove(self.private_key_file):
                return False
        if self.public_key_file and os.path.exists(self.public_key_file):
            if not fileremove(self.public_key_file):
                return False
        if self.certificate_file and os.path.exists(self.certificate_file):
            if not fileremove(self.certificate_file):
                return False
        return True


class SSHAuthenticator:
    # TODO, make independent known_hosts file path inside the corc directory

    def __init__(self, credentials=None, **kwargs):
        if not credentials:
            self._credentials = gen_ssh_credentials(**kwargs)
        else:
            self._credentials = credentials
        self._is_prepared = False

    @property
    def credentials(self):
        return self._credentials

    @property
    def is_prepared(self):
        return self._is_prepared

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

    def prepare(self, endpoint, allow_backauth=False):
        # Get the host key of the target endpoint
        host_key = self.get_host_key(endpoint)
        if self.add_to_known_hosts(endpoint, host_key):
            if allow_backauth:
                if self.add_to_authorized(endpoint):
                    self._is_prepared = True
            else:
                self._is_prepared = True
        return self.is_prepared

    def cleanup(self, endpoint, allow_backauth=False):
        is_cleaned = False
        credentials_removed = self.remove_credentials()
        known_host_removed = self.remove_from_known_hosts(endpoint)
        authorized_removed = False
        if allow_backauth:
            authorized_removed = self.remove_from_authorized(endpoint)

        if credentials_removed and known_host_removed:
            if allow_backauth:
                if authorized_removed:
                    self._credentials = None
                    self._is_prepared = False
                    is_cleaned = True
            else:
                self._credentials = None
                self._is_prepared = False
                is_cleaned = True
        return is_cleaned

    def add_to_authorized(self, path=None):
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".ssh", "authorized_keys")
        lock_path = "{}_lock".format(path)
        authorized_str = "{public_key}\n".format(public_key=self.credentials.public_key)
        authorized_lock = acquire_lock(lock_path)
        if write(path, authorized_str, mode="+a"):
            release_lock(authorized_lock)
            return True
        release_lock(authorized_lock)
        return False

    def get_authorized(self, path=None):
        if not path:
            path = os.path.join(os.path.expanduser("~", ".ssh", "authorized_keys"))

        content = [key.replace("\n", "") for key in fileload(path, readlines=True)]
        return content

    def remove_from_authorized(self, path=None):
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".ssh", "authorized_keys")
        lock_path = "{}_lock".format(path)
        authorized_lock = acquire_lock(lock_path)
        remove_content_from_file(path, self.credentials.public_key)
        release_lock(authorized_lock)
        return True

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
