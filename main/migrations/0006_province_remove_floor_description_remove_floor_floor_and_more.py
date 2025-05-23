# Generated by Django 5.2 on 2025-05-22 06:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_alter_application_city_alter_application_fio_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Province',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.RemoveField(
            model_name='floor',
            name='description',
        ),
        migrations.RemoveField(
            model_name='floor',
            name='floor',
        ),
        migrations.RemoveField(
            model_name='room',
            name='description',
        ),
        migrations.AlterField(
            model_name='room',
            name='currentOccupancy',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('province', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.province')),
            ],
        ),
    ]
