# Generated by Django 5.1.2 on 2024-11-12 15:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0012_rename_text_comment_content'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='content',
            new_name='text',
        ),
    ]
