# Manual migration to add missing deletion tracking fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0016_inventory_expiration_source_inventory_ingredient_key_and_more'),
    ]

    operations = [
        # These fields were already added in previous migrations (0009)
        # This migration is kept for compatibility but does nothing
    ]
