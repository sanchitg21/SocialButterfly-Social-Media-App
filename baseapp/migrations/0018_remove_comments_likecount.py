# Generated by Django 4.0.5 on 2022-07-01 14:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0017_comments_likecount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comments',
            name='LikeCount',
        ),
    ]