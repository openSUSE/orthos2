from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data", "0060_remove_machinegroup"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Vendor",
            new_name="Manufacturer",
        ),
        migrations.RenameField(
            model_name="platform",
            old_name="vendor",
            new_name="manufacturer",
        ),
        migrations.AlterModelOptions(
            name="platform",
            options={"ordering": ["manufacturer", "name"]},
        ),
    ]
