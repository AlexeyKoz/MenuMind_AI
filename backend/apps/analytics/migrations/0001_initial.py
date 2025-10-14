# Generated migration for analytics app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0005_add_archive_to_user_recipe'),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardCache',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4,
                 editable=False, primary_key=True, serialize=False)),
                ('period', models.CharField(choices=[('7days', 'Last 7 days'), ('30days', 'Last 30 days'), (
                    '90days', 'Last 90 days'), ('1year', 'Last year')], max_length=20)),
                ('shopping_data', models.JSONField(blank=True, default=dict)),
                ('recipes_data', models.JSONField(blank=True, default=dict)),
                ('inventory_data', models.JSONField(blank=True, default=dict)),
                ('nutrition_data', models.JSONField(
                    blank=True, default=dict, null=True)),
                ('achievements_data', models.JSONField(blank=True, default=dict)),
                ('ai_insights', models.JSONField(
                    blank=True, default=dict, null=True)),
                ('ai_generated_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                 related_name='dashboard_caches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'dashboard_cache',
            },
        ),
        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4,
                 editable=False, primary_key=True, serialize=False)),
                ('badge_id', models.CharField(choices=[('first_cook', 'First Cook'), ('chef_level_1', 'Chef Level 1'), ('chef_level_2', 'Chef Level 2'), ('chef_level_3', 'Chef Level 3'), ('master_chef', 'Master Chef'), ('streak_3', '3-Day Streak'), ('streak_7', '7-Day Streak'), ('streak_14', '14-Day Streak'), ('streak_30', '30-Day Streak'), ('streak_100', '100-Day Streak'), (
                    'protein_pro', 'Protein Pro'), ('balanced_eater', 'Balanced Eater'), ('consistent_logger', 'Consistent Logger'), ('budget_saver', 'Budget Saver'), ('smart_shopper', 'Smart Shopper'), ('deal_hunter', 'Deal Hunter'), ('waste_warrior', 'Waste Warrior'), ('zero_waste_week', 'Zero Waste Week'), ('organization_master', 'Organization Master')], max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('icon', models.CharField(max_length=10)),
                ('description', models.TextField()),
                ('earned_at', models.DateTimeField(auto_now_add=True)),
                ('notified', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                 related_name='achievements', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'achievements',
                'ordering': ['-earned_at'],
            },
        ),
        migrations.CreateModel(
            name='UserStreak',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4,
                 editable=False, primary_key=True, serialize=False)),
                ('streak_type', models.CharField(choices=[('nutrition_logging', 'Nutrition Logging'), (
                    'recipe_cooking', 'Recipe Cooking'), ('budget_tracking', 'Budget Tracking')], max_length=50)),
                ('current_count', models.IntegerField(default=0)),
                ('longest_count', models.IntegerField(default=0)),
                ('last_activity_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                 related_name='streaks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_streaks',
            },
        ),
        migrations.CreateModel(
            name='RecipeCookingLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4,
                 editable=False, primary_key=True, serialize=False)),
                ('cooked_at', models.DateTimeField(auto_now_add=True)),
                ('servings', models.IntegerField(default=1)),
                ('notes', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                 related_name='cooking_logs', to=settings.AUTH_USER_MODEL)),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                 related_name='cooking_logs', to='recipes.recipe')),
                ('canonical_recipe', models.ForeignKey(blank=True, null=True,
                 on_delete=django.db.models.deletion.CASCADE, related_name='cooking_logs', to='recipes.canonicalrecipe')),
            ],
            options={
                'db_table': 'recipe_cooking_logs',
                'ordering': ['-cooked_at'],
            },
        ),
        migrations.AddIndex(
            model_name='dashboardcache',
            index=models.Index(
                fields=['user', 'period'], name='dashboard_c_user_id_5e8ed7_idx'),
        ),
        migrations.AddIndex(
            model_name='dashboardcache',
            index=models.Index(fields=['expires_at'],
                               name='dashboard_c_expires_bb5a68_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='dashboardcache',
            unique_together={('user', 'period')},
        ),
        migrations.AddIndex(
            model_name='achievement',
            index=models.Index(
                fields=['user', '-earned_at'], name='achievement_user_id_f3c92a_idx'),
        ),
        migrations.AddIndex(
            model_name='achievement',
            index=models.Index(fields=['badge_id'],
                               name='achievement_badge_i_e91ad3_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='achievement',
            unique_together={('user', 'badge_id')},
        ),
        migrations.AddIndex(
            model_name='userstreak',
            index=models.Index(
                fields=['user', 'streak_type'], name='user_streak_user_id_c2c15a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='userstreak',
            unique_together={('user', 'streak_type')},
        ),
        migrations.AddIndex(
            model_name='recipecookinglog',
            index=models.Index(
                fields=['user', '-cooked_at'], name='recipe_cook_user_id_d15f6e_idx'),
        ),
        migrations.AddIndex(
            model_name='recipecookinglog',
            index=models.Index(fields=['recipe'],
                               name='recipe_cook_recipe__dac9ab_idx'),
        ),
    ]
