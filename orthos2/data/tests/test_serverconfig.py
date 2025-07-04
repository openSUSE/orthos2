from datetime import datetime

from django.test import TestCase

from orthos2.data.models import ServerConfig

SSH_KEYS = "ssh.keys.paths"
SSH_TIMEOUT = "ssh.timeout.seconds"
SSH_REMOTE_DIR = "ssh.scripts.remote.directory"
SSH_LOCAL_DIR = "ssh.scripts.local.directory"
VALID_DOMAIN_ENDINGS = "domain.validendings"
DAILY_EXECUTION_TIME = "tasks.daily.executiontime"
SMTP_RELAY = "mail.smtprelay.fqdn"


class GeneralManagerTest(TestCase):
    def test_get_ssh_keys(self) -> None:
        """Method should return SSH key paths as list, None otherwise."""
        assert ServerConfig.ssh.get_keys() is None

        ServerConfig(key=SSH_KEYS).save()
        assert ServerConfig.ssh.get_keys() is None
        ServerConfig.get_server_config_manager().filter(key=SSH_KEYS).delete()

        ServerConfig(key=SSH_KEYS, value="/tmp/a, /tmp/b").save()
        assert ServerConfig.ssh.get_keys() == ["/tmp/a", "/tmp/b"]
        ServerConfig.get_server_config_manager().filter(key=SSH_KEYS).delete()

    def test_get_ssh_timeout(self) -> None:
        """Method should return SSH timeout as integer, None otherwise."""
        assert ServerConfig.ssh.get_timeout() is None

        ServerConfig(key=SSH_TIMEOUT).save()
        assert ServerConfig.ssh.get_timeout() is None
        ServerConfig.get_server_config_manager().filter(key=SSH_TIMEOUT).delete()

        ServerConfig(key=SSH_TIMEOUT, value="foo").save()
        assert ServerConfig.ssh.get_timeout() is None
        ServerConfig.get_server_config_manager().filter(key=SSH_TIMEOUT).delete()

        ServerConfig(key=SSH_TIMEOUT, value=str(123)).save()
        assert ServerConfig.ssh.get_timeout() == 123
        ServerConfig.get_server_config_manager().filter(key=SSH_TIMEOUT).delete()

    def test_get_remote_scripts_dir(self) -> None:
        """Method should always return a path."""
        assert ServerConfig.ssh.get_remote_scripts_directory() == "/tmp/orthos2"

        ServerConfig(key=SSH_REMOTE_DIR).save()
        assert ServerConfig.ssh.get_remote_scripts_directory() == "/tmp/orthos2"
        ServerConfig.get_server_config_manager().filter(key=SSH_REMOTE_DIR).delete()

        ServerConfig(key=SSH_REMOTE_DIR, value="/tmp").save()
        assert ServerConfig.ssh.get_remote_scripts_directory() == "/tmp"
        ServerConfig.get_server_config_manager().filter(key=SSH_REMOTE_DIR).delete()

    def test_get_local_scripts_dir(self) -> None:
        """Method should always return a path."""
        assert (
            ServerConfig.ssh.get_local_scripts_directory() == "/usr/lib/orthos2/scripts"
        )

        ServerConfig(key=SSH_LOCAL_DIR).save()
        assert (
            ServerConfig.ssh.get_local_scripts_directory() == "/usr/lib/orthos2/scripts"
        )
        ServerConfig.get_server_config_manager().filter(key=SSH_LOCAL_DIR).delete()

        ServerConfig(key=SSH_LOCAL_DIR, value="/tmp").save()
        assert ServerConfig.ssh.get_local_scripts_directory() == "/tmp"
        ServerConfig.get_server_config_manager().filter(key=SSH_LOCAL_DIR).delete()

    def test_get_valid_domain_endings(self) -> None:
        """Method should return valid domain endings as list, None otherwise."""
        assert (
            ServerConfig.get_server_config_manager().get_valid_domain_endings() is None
        )

        ServerConfig(key=VALID_DOMAIN_ENDINGS).save()
        assert (
            ServerConfig.get_server_config_manager().get_valid_domain_endings() is None
        )
        ServerConfig.get_server_config_manager().filter(
            key=VALID_DOMAIN_ENDINGS
        ).delete()

        ServerConfig(key=VALID_DOMAIN_ENDINGS, value="test.bar, test.bar.foo").save()
        assert ServerConfig.get_server_config_manager().get_valid_domain_endings() == [
            "test.bar",
            "test.bar.foo",
        ]
        ServerConfig.get_server_config_manager().filter(
            key=VALID_DOMAIN_ENDINGS
        ).delete()

    def test_get_daily_execution_time(self) -> None:
        """Method should return a valid datetime.time object, None otherwise."""

        assert (
            ServerConfig.get_server_config_manager().get_daily_execution_time()
            == datetime(1900, 1, 1, 00, 00).time()
        )

        ServerConfig(key=DAILY_EXECUTION_TIME).save()
        assert (
            ServerConfig.get_server_config_manager().get_daily_execution_time()
            == datetime(1900, 1, 1, 00, 00).time()
        )
        ServerConfig.get_server_config_manager().filter(
            key=DAILY_EXECUTION_TIME
        ).delete()

        ServerConfig(key=DAILY_EXECUTION_TIME, value="foo").save()
        assert (
            ServerConfig.get_server_config_manager().get_daily_execution_time() is None
        )
        ServerConfig.get_server_config_manager().filter(
            key=DAILY_EXECUTION_TIME
        ).delete()

        ServerConfig(key=DAILY_EXECUTION_TIME, value="12:34").save()
        assert (
            ServerConfig.get_server_config_manager().get_daily_execution_time()
            == datetime(1900, 1, 1, 12, 34).time()
        )
        ServerConfig.get_server_config_manager().filter(
            key=DAILY_EXECUTION_TIME
        ).delete()

    def test_get_smtp_relay(self) -> None:
        """Method should return a FQDN to SMTP relay server, None otherwise."""
        assert ServerConfig.get_server_config_manager().get_smtp_relay() is None

        ServerConfig(key=SMTP_RELAY).save()
        assert ServerConfig.get_server_config_manager().get_smtp_relay() is None
        ServerConfig.get_server_config_manager().filter(key=SMTP_RELAY).delete()

        ServerConfig(key=SMTP_RELAY, value="foo.test.de").save()
        assert (
            ServerConfig.get_server_config_manager().get_smtp_relay() == "foo.test.de"
        )
        ServerConfig.get_server_config_manager().filter(key=SMTP_RELAY).delete()

    def test_bool_by_key(self) -> None:
        """Method should return `True` or `False`."""
        KEY = "bool_test"

        config, _ = ServerConfig.get_server_config_manager().get_or_create(
            key=KEY, value="bool:true"
        )

        self.assertEqual(
            ServerConfig.get_server_config_manager().bool_by_key(KEY), True
        )

        config.value = "bool:false"
        config.save()

        self.assertEqual(
            ServerConfig.get_server_config_manager().bool_by_key(KEY), False
        )

        config.value = "bool:foo"
        config.save()

        self.assertEqual(
            ServerConfig.get_server_config_manager().bool_by_key(KEY), False
        )

        config.value = "bar"
        config.save()

        self.assertEqual(
            ServerConfig.get_server_config_manager().bool_by_key(KEY), False
        )

        self.assertEqual(
            ServerConfig.get_server_config_manager().bool_by_key("foo"), False
        )
