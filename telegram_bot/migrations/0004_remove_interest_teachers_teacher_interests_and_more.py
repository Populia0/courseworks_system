# Generated by Django 5.1.1 on 2024-09-16 16:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0003_remove_topic_instructor_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interest',
            name='teachers',
        ),
        migrations.AddField(
            model_name='teacher',
            name='interests',
            field=models.ManyToManyField(to='telegram_bot.interest'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='courses',
            field=models.ManyToManyField(related_name='teachers', to='telegram_bot.course'),
        ),
    ]
