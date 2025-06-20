# Generated by Django 5.2 on 2025-04-13 05:36

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_transaction'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='type',
            new_name='name',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='name',
            field=models.CharField(default=django.utils.timezone.now, max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
