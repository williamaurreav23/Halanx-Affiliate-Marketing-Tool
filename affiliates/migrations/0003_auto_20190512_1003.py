# Generated by Django 2.2.1 on 2019-05-12 04:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('affiliates', '0002_auto_20190509_1923'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='affiliate',
            name='address',
        ),
        migrations.RemoveField(
            model_name='organisation',
            name='address',
        ),
        migrations.AddField(
            model_name='organisation',
            name='website',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.CreateModel(
            name='OrganisationAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_address', models.CharField(blank=True, max_length=200, null=True)),
                ('city', models.CharField(blank=True, max_length=200, null=True)),
                ('state', models.CharField(blank=True, max_length=200, null=True)),
                ('pincode', models.CharField(blank=True, max_length=200, null=True)),
                ('country', models.CharField(blank=True, max_length=200, null=True)),
                ('complete_address', models.TextField(blank=True, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('organisation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='organisation_address', to='affiliates.Organisation')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AffiliatePermanentAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_address', models.CharField(blank=True, max_length=200, null=True)),
                ('city', models.CharField(blank=True, max_length=200, null=True)),
                ('state', models.CharField(blank=True, max_length=200, null=True)),
                ('pincode', models.CharField(blank=True, max_length=200, null=True)),
                ('country', models.CharField(blank=True, max_length=200, null=True)),
                ('complete_address', models.TextField(blank=True, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('affiliate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='permanent_address', to='affiliates.Affiliate')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
