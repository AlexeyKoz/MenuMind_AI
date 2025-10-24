# Generated migration for multilingual shopping list support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0019_add_inventory_recipe_brief_cache'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoppingitem',
            name='name_translations',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text='Translated names for multilingual support: {"en": "tomato", "ru": "помидор", "he": "עגבנייה"}'
            ),
        ),
        migrations.AddField(
            model_name='shoppingitem',
            name='original_language',
            field=models.CharField(
                max_length=5,
                default='en',
                help_text='Language code of the original name field (en, ru, he)'
            ),
        ),
    ]
