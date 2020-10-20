import logging

from django.db import models

from orthos2.utils.misc import str_time_to_datetime

logger = logging.getLogger('models')


class BaseManager(models.Manager):

    def by_key(self, key):
        """Return the value by key."""
        try:
            obj = ServerConfig.objects.get(key=key)
            return obj.value
        except Exception as e:
            logger.error("Key '{}': {}".format(key, e))
        return None

    def bool_by_key(self, key):
        """
        Return a boolean value by key.

        Valid DB values are 'bool:true' (string) and 'bool:false'
        (string). If the value is not valid, `False` gets returned.
        """
        try:
            obj = ServerConfig.objects.get(key=key)

            if obj.value.lower() == 'bool:true':
                return True
        except Exception as e:
            logger.error("Key '{}': {}".format(key, e))
        return False

    def list_by_key(self, key, delimiter=','):
        """Return a list of strings seperated by `delimiter`."""
        try:
            obj = ServerConfig.objects.get(key=key)

            if obj.value:
                return [value.strip() for value in obj.value.split(delimiter)]
            else:
                return []
        except Exception as e:
            logger.error("Key '{}': {}".format(key, e))
        return None

    def get_smtp_relay(self):
        """Return the FQDN of the SMTP relay server."""
        try:
            obj = ServerConfig.objects.get(key='mail.smtprelay.fqdn')

            if obj.value:
                return obj.value
            else:
                logger.warning("SMTP relay entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No SMTP relay server entry found")
        return None

    def get_valid_domain_endings(self):
        """Return a list of valid domain endings."""
        try:
            obj = ServerConfig.objects.get(key='domain.validendings')

            if obj.value:
                return [value.strip() for value in obj.value.split(',')]
            else:
                logger.warning("Valid domain endings entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No valid domain endings entry found")
        return None

    def get_daily_execution_time(self):
        """
        Return the execution time when daily tasks should be executed as datetime.time
        object.
        """
        try:
            obj = ServerConfig.objects.get(key='tasks.daily.executiontime')

            if obj.value:
                execution_time = str_time_to_datetime(obj.value)
                if execution_time:
                    return execution_time.time()
                else:
                    logger.warning("Daily exection time entry is no valid time string (HH:MM)")
            else:
                logger.warning("Daily execution time entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No daily execution time entry found")
        return None


class SSHManager(BaseManager):

    def get_keys(self):
        """Return a list of file paths to SSH master keys for SSH authentication."""
        try:
            obj = ServerConfig.objects.get(key='ssh.keys.paths')

            if obj.value:
                return [value.strip() for value in obj.value.split(',')]
            else:
                logger.warning("SSH key paths entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No SSH key paths entry found")
        return None

    def get_timeout(self):
        """Return the timeout in seconds for SSH connection attempts as integer."""
        try:
            obj = ServerConfig.objects.get(key='ssh.timeout.seconds')

            if obj.value:
                return int(obj.value)
            else:
                logger.warning("SSH timeout entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No SSH timeout entry found")
        except ValueError:
            logger.error("SSH timeout value is no number/integer")
        return None

    def get_remote_scripts_directory(self):
        """Return a path where remote executed scripts (host side) should be placed."""
        try:
            obj = ServerConfig.objects.get(key='ssh.scripts.remote.directory')

            if obj.value:
                return obj.value
            else:
                logger.warning("Remote scripts directory entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No remote scripts directory entry found")
        return None

    def get_local_scripts_directory(self):
        """Return a path to the local scripts directory (server side)."""
        try:
            obj = ServerConfig.objects.get(key='ssh.scripts.local.directory')

            if obj.value:
                return obj.value
            else:
                logger.warning("Local scripts directory entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No local scripts directory entry found")
        return None


class ServerConfig(models.Model):

    class Meta:
        ordering = ['key']
        verbose_name = 'Server Configuration'

    key = models.CharField(
        max_length=100,
        unique=True
    )

    value = models.CharField(
        max_length=512,
        blank=True
    )

    created = models.DateTimeField('created at', auto_now=True)

    objects = BaseManager()
    ssh = SSHManager()

    def __str__(self):
        return self.key
