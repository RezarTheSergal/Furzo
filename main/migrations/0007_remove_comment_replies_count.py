# Generated by Django 5.2.3 on 2025-07-04 20:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_alter_comment_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='replies_count',
        ),
    ]
