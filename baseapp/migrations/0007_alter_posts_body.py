# Generated by Django 4.0.3 on 2022-04-16 13:07

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0006_remove_posts_hascomment_posts_commentcount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='posts',
            name='Body',
            field=models.CharField(max_length=1000),
        ),
    ]
