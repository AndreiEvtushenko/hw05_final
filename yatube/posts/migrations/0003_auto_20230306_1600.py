# Generated by Django 2.2.16 on 2023-03-06 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20230306_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name='Дата создания'),
        ),
        migrations.AlterField(
            model_name='post',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name='Дата создания'),
        ),
    ]