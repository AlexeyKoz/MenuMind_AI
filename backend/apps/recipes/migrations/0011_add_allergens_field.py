# Generated migration to add allergens field to recipes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0010_add_enhanced_performance_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='canonicalrecipe',
            name='allergens',
            field=models.JSONField(
                blank=True, default=list, help_text='List of allergens: ["dairy", "eggs", "fish", "shellfish", "tree_nuts", "peanuts", "wheat", "gluten", "soy", "sesame"]'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='allergens',
            field=models.JSONField(
                blank=True, default=list, help_text='List of allergens detected in this recipe'),
        ),
    ]
