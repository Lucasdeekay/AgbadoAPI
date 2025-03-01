# Generated by Django 5.1.1 on 2025-01-17 22:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0003_alter_user_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_picture/'),
        ),
        migrations.AddField(
            model_name='user',
            name='referral_code',
            field=models.CharField(blank=True, max_length=15, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='state',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='kyc',
            name='driver_license',
            field=models.ImageField(blank=True, null=True, upload_to='driver_license/'),
        ),
        migrations.AlterField(
            model_name='kyc',
            name='national_id',
            field=models.ImageField(blank=True, null=True, upload_to='national_id/'),
        ),
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('referer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_referer', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
