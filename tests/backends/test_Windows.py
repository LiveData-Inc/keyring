import sys

import pytest

import keyring.backends.Windows
from keyring.testing.backend import UNICODE_CHARS, BackendBasicTests


@pytest.mark.skipif(
    not keyring.backends.Windows.WinVaultKeyring.viable, reason="Needs Windows"
)
class TestWinVaultKeyring(BackendBasicTests):
    def tearDown(self):
        # clean up any credentials created
        for cred in self.credentials_created:
            try:
                self.keyring.delete_password(*cred)
            except Exception as e:
                print(e, file=sys.stderr)

    def init_keyring(self):
        return keyring.backends.Windows.WinVaultKeyring()

    def set_utf8_password(self, service, username, password):
        """
        Write a UTF-8 encoded password using win32ctypes primitives
        """
        from ctypes import c_char, cast, create_string_buffer, sizeof

        from win32ctypes.core import _authentication as auth
        from win32ctypes.core.ctypes._common import LPBYTE

        credential = dict(
            Type=1,
            TargetName=service,
            UserName=username,
            CredentialBlob=password,
            Comment="Stored using python-keyring",
            Persist=3,
        )

        c_cred = auth.CREDENTIAL.fromdict(credential, 0)
        blob_data = create_string_buffer(password.encode("utf-8"))
        c_cred.CredentialBlobSize = sizeof(blob_data) - sizeof(c_char)
        c_cred.CredentialBlob = cast(blob_data, LPBYTE)
        c_cred_pointer = auth.PCREDENTIAL(c_cred)
        auth._CredWrite(c_cred_pointer, 0)

        self.credentials_created.add((service, username))

    def test_long_password_nice_error(self):
        self.keyring.set_password('system', 'user', 'x' * 512 * 2)

    def test_read_utf8_password(self):
        """
        Write a UTF-8 encoded credential and make sure it can be read back correctly.
        """
        service = "keyring-utf8-test"
        username = "keyring"
        password = "utf8-test" + UNICODE_CHARS

        self.keyring.set_password(service, username, password)
        assert self.keyring.get_password(service, username) == password
        self.keyring.delete_password(service, username)

    def test_long_password_nice_error(self):
        self.keyring.set_password('system', 'user', 'x' * 10000)
        self.keyring.delete_password('system', 'user')

    def test_long_password_too_long_nice_error(self):
        with pytest.raises(ValueError) as exc_info:
            self.keyring.set_password('system', 'user', 'x' * (2 ** 20 + 1))
            self.keyring.delete_password('system', 'user')

        assert exc_info.type is ValueError and exc_info.value.args[0] == 2 ** 20


@pytest.mark.skipif('sys.platform != "win32"')
def test_winvault_always_viable():
    """
    The WinVault backend should always be viable on Windows.
    """
    assert keyring.backends.Windows.WinVaultKeyring.viable
