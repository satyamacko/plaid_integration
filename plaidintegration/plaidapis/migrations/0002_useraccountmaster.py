# Generated by Django 3.1.2 on 2020-10-24 07:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plaidapis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAccountMaster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.CharField(max_length=128)),
                ('mask', models.CharField(max_length=32, null=True)),
                ('account_name', models.CharField(max_length=128)),
                ('account_official_name', models.CharField(max_length=128, null=True)),
                ('type', models.CharField(max_length=128)),
                ('subtype', models.CharField(max_length=128)),
                ('user_plaid_master', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='plaidapis.userplaidmaster')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]