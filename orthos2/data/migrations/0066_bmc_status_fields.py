import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0065_alter_remotepower_fence_agent"),
    ]

    operations = [
        migrations.AddField(
            model_name="bmc",
            name="status_ipv4",
            field=models.SmallIntegerField(
                choices=[
                    (0, "unreachable"),
                    (1, "reachable"),
                    (2, "confirmed"),
                    (3, "MAC mismatch"),
                    (4, "address mismatch"),
                    (5, "no address assigned"),
                    (6, "address-family disabled"),
                ],
                default=0,
                editable=False,
                help_text="Does this IPv4 address respond to ping?",
                verbose_name="Status IPv4",
            ),
        ),
        migrations.AddField(
            model_name="bmc",
            name="status_ipv6",
            field=models.SmallIntegerField(
                choices=[
                    (0, "unreachable"),
                    (1, "reachable"),
                    (2, "confirmed"),
                    (3, "MAC mismatch"),
                    (4, "address mismatch"),
                    (5, "no address assigned"),
                    (6, "address-family disabled"),
                ],
                default=0,
                editable=False,
                help_text="Does this IPv6 address respond to ping?",
                verbose_name="Status IPv6",
            ),
        ),
        migrations.AddField(
            model_name="bmc",
            name="last_check",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2016, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc
                ),
                editable=False,
                verbose_name="Checked at",
            ),
        ),
    ]
