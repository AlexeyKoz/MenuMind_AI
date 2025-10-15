# Manual migration to add missing deletion tracking fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0016_inventory_expiration_source_inventory_ingredient_key_and_more'),
    ]

    operations = [
        # Add missing fields to ShoppingList
        migrations.AddField(
            model_name='shoppinglist',
            name='deletion_warning_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='deletion_warning_sent_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='last_activity',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add missing field to ShoppingListCollaborator
        migrations.AddField(
            model_name='shoppinglistcollaborator',
            name='items_added_count',
            field=models.IntegerField(default=0),
        ),
    ]
