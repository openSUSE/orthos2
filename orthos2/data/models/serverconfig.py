import datetime
import logging
from typing import List, Optional

from django.db import models

from orthos2.utils.misc import str_time_to_datetime

logger = logging.getLogger("models")


class ServerConfigManager(models.Manager["ServerConfig"]):
    def by_key(self, key: str, fallback: Optional[str] = None) -> Optional[str]:
        """Return the value by key."""
        try:
            obj: ServerConfig
            obj, created = ServerConfig.objects.get_or_create(
                key=key, defaults={"value": fallback}
            )
            if created:
                logger.info("Created serverconfig entry: %s -> %s", key, fallback)
            return obj.value
        except Exception as e:
            logger.exception("Key '%s': %s", key, e)
        return fallback

    def bool_by_key(self, key: str, fallback: bool = False) -> bool:
        """
        Return a boolean value by key.

        Valid DB values are 'bool:true' and 'bool:false' (both strings). If the value is not valid, `False` gets
        returned.

        :param key: The key to retrieve.
        :param fallback: Returns false per default in case the key doesn't exist.
        :returns: True in case the boolean in the database is true.
        """
        try:
            obj = ServerConfig.objects.get(key=key)
            return obj.value.lower() == "bool:true"
        except ServerConfig.DoesNotExist as e:
            logger.warning('Key "%s" did not exist, returning fallback value', key, e)
            return fallback

    def list_by_key(self, key: str, delimiter: str = ",") -> Optional[List[str]]:
        """Return a list of strings seperated by `delimiter`."""
        try:
            obj = ServerConfig.objects.get(key=key)

            if obj.value:
                return [value.strip() for value in obj.value.split(delimiter)]
            else:
                return []
        except Exception as e:
            logger.exception("Key '%s': %s", key, e)
        return None

    def get_smtp_relay(self) -> Optional[str]:
        """Return the FQDN of the SMTP relay server."""
        try:
            obj: Optional[ServerConfig]
            obj = ServerConfig.objects.get(key="mail.smtprelay.fqdn")

            if obj and obj.value:
                return obj.value
            else:
                logger.warning("SMTP relay entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No SMTP relay server entry found")
        return None

    def get_valid_domain_endings(self) -> Optional[List[str]]:
        """Return a list of valid domain endings."""
        try:
            obj = ServerConfig.objects.get(key="domain.validendings")

            if obj.value:
                return [value.strip() for value in obj.value.split(",")]
            else:
                logger.warning("Valid domain endings entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No valid domain endings entry found")
        return None

    def get_daily_execution_time(self) -> Optional[datetime.time]:
        """
        Return the execution time when daily tasks should be executed as datetime.time
        object.
        """
        try:
            obj = ServerConfig.objects.get(key="tasks.daily.executiontime")

            if obj.value:
                execution_time = str_time_to_datetime(obj.value)
                if execution_time:
                    return execution_time.time()
                else:
                    logger.warning(
                        "Daily exection time entry is no valid time string (HH:MM)"
                    )
            else:
                logger.warning("Daily execution time entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No daily execution time entry found")
        return None


class ServerConfigSSHManager(ServerConfigManager):
    def get_keys(self) -> Optional[List[str]]:
        """Return a list of file paths to SSH master keys for SSH authentication."""
        try:
            obj = ServerConfig.objects.get(key="ssh.keys.paths")

            if obj.value:
                return [value.strip() for value in obj.value.split(",")]
            else:
                logger.warning("SSH key paths entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No SSH key paths entry found")
        return None

    def get_timeout(self) -> Optional[int]:
        """Return the timeout in seconds for SSH connection attempts as integer."""
        try:
            obj = ServerConfig.objects.get(key="ssh.timeout.seconds")

            if obj.value:
                return int(obj.value)
            else:
                logger.warning("SSH timeout entry is empty")
        except ServerConfig.DoesNotExist:
            logger.warning("No SSH timeout entry found")
        except ValueError:
            logger.exception("SSH timeout value is no number/integer")
        return None

    def get_remote_scripts_directory(self) -> str:
        """Return a path where remote executed scripts (host side) should be placed."""
        default_scripts_directory = "/tmp/orthos2"
        try:
            obj: Optional[ServerConfig]
            obj = ServerConfig.objects.get(key="ssh.scripts.remote.directory")

            if obj and obj.value:
                return obj.value
            else:
                logger.warning(
                    "Remote scripts directory entry is empty, returning %s",
                    default_scripts_directory,
                )
        except ServerConfig.DoesNotExist:
            logger.info(
                "No remote scripts directory entry found, returning %s",
                default_scripts_directory,
            )
        return default_scripts_directory

    def get_local_scripts_directory(self) -> str:
        """Return a path to the local scripts directory (server side)."""
        default_scripts_directory = "/usr/lib/orthos2/scripts"
        try:
            obj: Optional[ServerConfig]
            obj = ServerConfig.objects.get(key="ssh.scripts.local.directory")

            if obj and obj.value:
                return obj.value
            else:
                logger.info(
                    "Local scripts directory entry is empty, returning %s",
                    default_scripts_directory,
                )
        except ServerConfig.DoesNotExist:
            logger.info(
                "No local scripts directory entry found, returning %s",
                default_scripts_directory,
            )
        return default_scripts_directory


class ServerConfig(models.Model):
    class Meta:
        ordering = ["key"]
        verbose_name = "Server Configuration"

    key = models.CharField(max_length=100, unique=True)

    value = models.CharField(max_length=512, blank=True)

    objects = ServerConfigManager()
    ssh = ServerConfigSSHManager()

    def __str__(self) -> str:
        return self.key
