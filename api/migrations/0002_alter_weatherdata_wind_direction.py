# Generated by Django 5.2 on 2025-05-07 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weatherdata',
            name='wind_direction',
            field=models.CharField(max_length=20),
        ),
    ]
