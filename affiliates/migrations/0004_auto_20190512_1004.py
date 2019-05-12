# Generated by Django 2.2.1 on 2019-05-12 04:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('affiliates', '0003_auto_20190512_1003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affiliatepermanentaddress',
            name='affiliate',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='address', to='affiliates.Affiliate'),
        ),
        migrations.AlterField(
            model_name='organisationaddress',
            name='organisation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='address', to='affiliates.Organisation'),
        ),
    ]
