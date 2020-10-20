import datetime
import logging

from orthos2.data.models import Machine
from django.conf import settings
from django.contrib.auth.models import User
from orthos2.taskmanager.models import Task
from orthos2.utils.misc import send_email

logger = logging.getLogger('tasks')


class SendRestoredPassword(Task):
    """Generate the email with the restored password for a user and sends it."""

    def __init__(self, user_id, new_password):
        self.user_id = user_id
        self.new_password = new_password

    def execute(self):
        """Execute the task."""
        try:
            user = User.objects.get(pk=self.user_id)

            subject = "Orthos password restored"
            message = """Hi {username},

Your Orthos password has been restored.

  Login:    {username}
  Password: {password}


Regards,
Orthos""".format(
                username=user.username,
                password=self.new_password
            )

            send_email(user.email, subject, message)

        except User.DoesNotExist:
            logger.error("User not found: id={}".format(self.user_id))
        except Exception as e:
            logger.exception(e)


class SendReservationInformation(Task):
    """Generate reservation information email for user and sends it."""

    def __init__(self, user_id, fqdn):
        self.user_id = user_id
        self.fqdn = fqdn

    def execute(self):
        """Execute the task."""
        try:
            user = User.objects.get(pk=self.user_id)
            machine = Machine.objects.get(fqdn=self.fqdn)

            subject = "Reservation of {}".format(machine.fqdn)
            message = """Hi {username},

The machine {fqdn} was just reserved for you.

To login, just SSH to {fqdn} or {ip}.

If you have any problems, contact <{support_contact}>.""".format(
                username=user.username,
                fqdn=machine.fqdn,
                ip=machine.ipv4,
                support_contact=machine.get_support_contact()
            )

            if machine.has_remotepower():
                message += """

To reset the machine if the kernel has crashed, you can use the remote power
switch capability. Just use the Orthos web interface at:

  {url}

Or use the following commandline interface command:

  (orthos) POWER {fqdn} REBOOT""".format(
                    url=settings.BASE_URL + '/machine/' + str(machine.pk),
                    fqdn=machine.fqdn
                )

            if machine.has_serialconsole():
                message += """

For a serial console, establish a SSH login on {serialconsole_fqdn} and
follow the instructions on the screen.""".format(
                    serialconsole_fqdn=machine.serialconsole.cscreen_server.fqdn
                )

            message += """

Remember that the machine reservation ends at {reserved_until}. You'll get
another email as reminder one day before the machine gets released automatically.
Information about Orthos can be found here: http://orthos-host.domain.de/


Regards,
Orthos""".format(
                reserved_until=machine.reserved_until
            )

            send_email(user.email, subject, message)

        except User.DoesNotExist:
            logger.error("User not found: id={}".format(self.user_id))
        except Machine.DoesNotExist:
            logger.error("Machine does not exist: fqdn={}".format(self.fqdn))
        except Exception as e:
            logger.exception(e)


class CheckReservationExpiration(Task):
    """
    Task that checks for a expiring reservation for one machine.

    Emails get sent five, two and one day(s) before plus the day of expiration. If the expiration
    date was yesterday, then we delete the reservation (release).
    """

    def __init__(self, fqdn):
        self.fqdn = fqdn

    def execute(self):
        """Execute the task."""
        today = datetime.date.today()

        try:
            machine = Machine.objects.get(fqdn=self.fqdn)

            if not machine.reserved_by:
                return

            user = machine.reserved_by
            delta = machine.reserved_until.date() - today

            if delta.days > 5 or delta.days in {4, 3}:
                logger.debug("{}d left for {}@{}".format(
                    delta.days,
                    user.username,
                    machine.fqdn
                ))
                return

            if delta.days < 0:
                # release machine and return
                machine.release(user)
                return

            elif delta.days == 1:
                subject = "Reservation of {} expires tomorrow".format(machine.fqdn)
            elif delta.days == 0:
                subject = "Reservation of {} expires today".format(machine.fqdn)
            else:
                subject = "Reservation of {} expires in {} days".format(machine.fqdn, delta.days)

            message = """Hi {username},

The machine reservation for {fqdn} expires at {reserved_until}.

If you need the machine longer, you can just extend the reservation. Just use
the Orthos web interface at:

  {url}

Or use the following commandline interface command:

  (orthos) RESERVE {fqdn}

Please note, that the machine will be setup after reservation expired!

If you have any problems, contact <{support_contact}>.


Regards,
Orthos""".format(
                username=user.username,
                fqdn=machine.fqdn,
                reserved_until=machine.reserved_until,
                url=settings.BASE_URL + '/machine/' + str(machine.pk),
                support_contact=machine.get_support_contact()
            )

            send_email(user.email, subject, message)

        except User.DoesNotExist:
            logger.error("User not found: id={}".format(self.user_id))
        except Machine.DoesNotExist:
            logger.error("Machine does not exist: fqdn={}".format(self.fqdn))
        except Exception as e:
            logger.exception(e)


class CheckMultipleAccounts(Task):
    """
    Inform a user that there are multiple accounts sharing the same email address (local part).

    Example:
        orthos@bar.foo
        orthos@bar.baz
    """

    def __init__(self, user_id):
        self.user_id = user_id

    def execute(self):
        """Execute the task."""
        try:
            user = User.objects.get(pk=self.user_id)

            prefix = user.email.split('@')[0] + '@'
            usernames = list(
                User.objects.filter(email__startswith=prefix).values('username', 'email')
            )

            if len(usernames) <= 1:
                return

            subject = "Multiple Accounts found!"
            message = """Hi {username},

We found multiple accounts related to your email address (local part):

{usernames}

Please send a short email to <{contact}> and tell which accounts are in use at
the moment.

This information is needed in order to make Orthos great again!


Regards,
Orthos""".format(
                username=user.username,
                usernames="\n".join(
                    ['  {} ({})'.format(user['username'], user['email']) for user in usernames]
                ),
                contact=settings.CONTACT
            )

            send_email(user.email, subject, message)

        except User.DoesNotExist:
            logger.error("User not found: id={}".format(self.user_id))
        except Exception as e:
            logger.exception(e)
