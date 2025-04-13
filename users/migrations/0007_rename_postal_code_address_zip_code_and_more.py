from django.db import migrations, models
import django.utils.timezone

def set_default_created_at(apps, schema_editor):
    Address = apps.get_model('users', 'Address')
    Profile = apps.get_model('users', 'Profile')
    PaymentMethod = apps.get_model('users', 'PaymentMethod')
    
    for obj in Address.objects.all():
        obj.created_at = django.utils.timezone.now()
        obj.save()
    
    for obj in Profile.objects.all():
        obj.created_at = django.utils.timezone.now()
        obj.save()
    
    for obj in PaymentMethod.objects.all():
        obj.created_at = django.utils.timezone.now()
        obj.save()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_favorite_product_alter_favorite_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='Address',
            old_name='postal_code',
            new_name='zip_code',
        ),
        migrations.AddField(
            model_name='Address',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='PaymentMethod',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='Profile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='Profile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='CustomUser',
            name='secret_code',
            field=models.CharField(blank=True, max_length=36, null=True),
        ),
    ]