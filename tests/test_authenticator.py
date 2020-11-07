import os
import unittest

from corc.authenticator import SSHAuthenticator, gen_ssh_credentials


class TestAuthenticator(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
        self.test_ssh_dir = os.path.join(self.test_dir, "ssh")
        self.tmp_credentials = gen_ssh_credentials(ssh_dir_path=self.test_ssh_dir)
        self.authenticator = SSHAuthenticator(credentials=self.tmp_credentials)

    def tearDown(self):
        self.tmp_credentials = None
        self.authenticator = None

    def test_instance_authorized_keys(self):
        authorized_keys_path = os.path.join(self.test_ssh_dir, "authorized_keys")
        self.assertTrue(self.authenticator.add_to_authorized(path=authorized_keys_path))
        # Load the
        authorized_keys = self.authenticator.get_authorized(path=authorized_keys_path)
        self.assertIn(self.authenticator.credentials.public_key, authorized_keys)
        self.assertTrue(
            self.authenticator.remove_from_authorized(path=authorized_keys_path)
        )


if __name__ == "__main__":
    unittest.main()
