# Generated by Django 5.1.2 on 2024-11-11 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('News', '0010_remove_submission_comments_comment_author_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='comments',
            field=models.ManyToManyField(blank=True, related_name='submissions', to='News.comment'),
        ),
    ]