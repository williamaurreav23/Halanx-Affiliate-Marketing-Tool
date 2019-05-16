# Generated by Django 2.2.1 on 2019-05-16 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('referrals', '0005_auto_20190516_1846'),
    ]

    operations = [
        migrations.AddField(
            model_name='houseownerreferral',
            name='house_type',
            field=models.CharField(blank=True, choices=[('apartment', 'Apartment'), ('independent', 'Independent House'), ('villa', 'Villa')], max_length=20, null=True),
        ),
    ]
