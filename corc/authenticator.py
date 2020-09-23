import paramiko
from io import StringIO


def gen_rsa_ssh_key_pair(size=2048):
    rsa_key = paramiko.RSAKey.generate(size)
    string_io_obj = StringIO()
    rsa_key.write_private_key(string_io_obj)

    private_key = string_io_obj.getvalue()
    public_key = ("ssh-rsa %s" % (rsa_key.get_base64())).strip()
    return private_key, public_key


class SSHCredentials:
    def __init__(self, user=None, password=None, private_key=None, public_key=None):
        self.user = user
        self.password = password
        self.private_key = private_key
        self.public_key = public_key

        @property
        def user(self):
            return self.user

        @property
        def password(self):
            return self.password

        @property
        def private_key(self):
            return self.private_key

        @property
        def public_key(self):
            return self.public_key


class SSHAuthenticator:
    def __init__(self, credentials=None):
        if not credentials:
            private_key, public_key = gen_rsa_ssh_key_pair()
            self.credentials = SSHCredentials(
                private_key=private_key, public_key=public_key
            )
        else:
            self.credentials = credentials

    @property
    def credentials(self):
        return self.credentials
