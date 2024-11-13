# Generated by Django 5.1.2 on 2024-11-12 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0008_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(default='avatars/default_avatar.png', max_length=255, upload_to='avatars/'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='banner',
            field=models.ImageField(default='banners/default_banner.jpg', max_length=255, upload_to='banners/'),
        ),
    ]