# Generated by Django 5.1.7 on 2025-04-13 16:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_order_updated_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='card_cvv',
        ),
        migrations.RemoveField(
            model_name='order',
            name='card_expiry',
        ),
        migrations.RemoveField(
            model_name='order',
            name='card_holder',
        ),
        migrations.RemoveField(
            model_name='order',
            name='card_number',
        ),
        migrations.RemoveField(
            model_name='order',
            name='phone_number',
        ),
    ]
