# Generated by Django 4.0.3 on 2022-04-29 12:57

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0010_alter_pages_about_alter_posts_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdetails',
            name='Gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female')], max_length=100),
        ),
    ]
