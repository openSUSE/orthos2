from orthos2.data.models import ServerConfig
from django.test import TestCase

SSH_KEYS = 'ssh.keys.paths'
SSH_TIMEOUT = 'ssh.timeout.seconds'
SSH_REMOTE_DIR = 'ssh.scripts.remote.directory'
SSH_LOCAL_DIR = 'ssh.scripts.local.directory'
VALID_DOMAIN_ENDINGS = 'domain.validendings'
DAILY_EXECUTION_TIME = 'tasks.daily.executiontime'
SMTP_RELAY = 'mail.smtprelay.fqdn'


class GeneralManagerTest(TestCase):

    def test_get_ssh_keys(self):
        """Method should return SSH key paths as list, None otherwise."""
        assert ServerConfig.ssh.get_keys() is None

        ServerConfig(key=SSH_KEYS).save()
        assert ServerConfig.ssh.get_keys() is None
        ServerConfig.objects.filter(key=SSH_KEYS).delete()

        ServerConfig(
            key=SSH_KEYS,
            value='/tmp/a, /tmp/b'
        ).save()
        assert ServerConfig.ssh.get_keys() == ['/tmp/a', '/tmp/b']
        ServerConfig.objects.filter(key=SSH_KEYS).delete()

    def test_get_ssh_timeout(self):
        """Method should return SSH timeout as integer, None otherwise."""
        assert ServerConfig.ssh.get_timeout() is None

        ServerConfig(key=SSH_TIMEOUT).save()
        assert ServerConfig.ssh.get_timeout() is None
        ServerConfig.objects.filter(key=SSH_TIMEOUT).delete()

        ServerConfig(key=SSH_TIMEOUT, value='foo').save()
        assert ServerConfig.ssh.get_timeout() is None
        ServerConfig.objects.filter(key=SSH_TIMEOUT).delete()

        ServerConfig(key=SSH_TIMEOUT, value=123).save()
        assert ServerConfig.ssh.get_timeout() == 123
        ServerConfig.objects.filter(key=SSH_TIMEOUT).delete()

    def test_get_remote_scripts_dir(self):
        """Method should return a path, None otherwise."""
        assert ServerConfig.ssh.get_remote_scripts_directory() is None

        ServerConfig(key=SSH_REMOTE_DIR).save()
        assert ServerConfig.ssh.get_remote_scripts_directory() is None
        ServerConfig.objects.filter(key=SSH_REMOTE_DIR).delete()

        ServerConfig(key=SSH_REMOTE_DIR, value='/tmp').save()
        assert ServerConfig.ssh.get_remote_scripts_directory() == '/tmp'
        ServerConfig.objects.filter(key=SSH_REMOTE_DIR).delete()

    def test_get_local_scripts_dir(self):
        """Method should return a path, None otherwise."""
        assert ServerConfig.ssh.get_local_scripts_directory() is None

        ServerConfig(key=SSH_LOCAL_DIR).save()
        assert ServerConfig.ssh.get_local_scripts_directory() is None
        ServerConfig.objects.filter(key=SSH_LOCAL_DIR).delete()

        ServerConfig(key=SSH_LOCAL_DIR, value='/tmp').save()
        assert ServerConfig.ssh.get_local_scripts_directory() == '/tmp'
        ServerConfig.objects.filter(key=SSH_LOCAL_DIR).delete()

    def test_get_valid_domain_endings(self):
        """Method should return valid domain endings as list, None otherwise."""
        assert ServerConfig.objects.get_valid_domain_endings() is None

        ServerConfig(key=VALID_DOMAIN_ENDINGS).save()
        assert ServerConfig.objects.get_valid_domain_endings() is None
        ServerConfig.objects.filter(key=VALID_DOMAIN_ENDINGS).delete()

        ServerConfig(
            key=VALID_DOMAIN_ENDINGS,
            value='test.bar, test.bar.foo'
        ).save()
        assert ServerConfig.objects.get_valid_domain_endings() == ['test.bar', 'test.bar.foo']
        ServerConfig.objects.filter(key=VALID_DOMAIN_ENDINGS).delete()

    def test_get_daily_execution_time(self):
        """Method should return a valid datetime.time object, None otherwise."""
        from datetime import datetime

        assert ServerConfig.objects.get_daily_execution_time() is None

        ServerConfig(key=DAILY_EXECUTION_TIME).save()
        assert ServerConfig.objects.get_daily_execution_time() is None
        ServerConfig.objects.filter(key=DAILY_EXECUTION_TIME).delete()

        ServerConfig(key=DAILY_EXECUTION_TIME, value='foo').save()
        assert ServerConfig.objects.get_daily_execution_time() is None
        ServerConfig.objects.filter(key=DAILY_EXECUTION_TIME).delete()

        ServerConfig(key=DAILY_EXECUTION_TIME, value='12:34').save()
        assert ServerConfig.objects.get_daily_execution_time() == \
            datetime(1900, 1, 1, 12, 34).time()
        ServerConfig.objects.filter(key=DAILY_EXECUTION_TIME).delete()

    def test_get_smtp_relay(self):
        """Method should return a FQDN to SMTP relay server, None otherwise."""
        assert ServerConfig.objects.get_smtp_relay() is None

        ServerConfig(key=SMTP_RELAY).save()
        assert ServerConfig.objects.get_smtp_relay() is None
        ServerConfig.objects.filter(key=SMTP_RELAY).delete()

        ServerConfig(key=SMTP_RELAY, value='foo.test.de').save()
        assert ServerConfig.objects.get_smtp_relay() == 'foo.test.de'
        ServerConfig.objects.filter(key=SMTP_RELAY).delete()

    def test_bool_by_key(self):
        """Method should return `True` or `False`."""
        KEY = 'bool_test'

        config, _ = ServerConfig.objects.get_or_create(key=KEY, value='bool:true')

        self.assertEqual(ServerConfig.objects.bool_by_key(KEY), True)

        config.value = 'bool:false'
        config.save()

        self.assertEqual(ServerConfig.objects.bool_by_key(KEY), False)

        config.value = 'bool:foo'
        config.save()

        self.assertEqual(ServerConfig.objects.bool_by_key(KEY), False)

        config.value = 'bar'
        config.save()

        self.assertEqual(ServerConfig.objects.bool_by_key(KEY), False)

        self.assertEqual(ServerConfig.objects.bool_by_key('foo'), False)
