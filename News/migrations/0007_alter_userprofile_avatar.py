# Generated by Django 5.1.2 on 2024-10-24 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0006_alter_userprofile_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(default='avatars/default_avatar.png', upload_to='avatars/'),
        ),
    ]
