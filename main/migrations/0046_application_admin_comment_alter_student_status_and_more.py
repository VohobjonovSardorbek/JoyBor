# Generated by Django 5.2 on 2025-07-26 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0045_alter_student_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='admin_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='status',
            field=models.CharField(choices=[('Qarzdor', 'Qarzdor'), ('Haqdor', 'Haqdor'), ('Tekshirilmaydi', 'Tekshirilmaydi')], default='Qarzdor', max_length=120),
        ),
        migrations.DeleteModel(
            name='AnswerForApplication',
        ),
    ]
