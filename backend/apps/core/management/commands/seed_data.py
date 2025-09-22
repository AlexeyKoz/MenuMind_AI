from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.shopping.models import ShoppingList, ShoppingItem
import random
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding database with initial data...')

        # Create test users
        self.create_test_users()

        # Create shopping lists and items
        self.create_shopping_data()

        # Skip nutrition and AI data for now since models don't exist yet
        self.stdout.write(
            '⏭️ Skipping nutrition and AI data (models not implemented yet)')

        self.stdout.write(
            self.style.SUCCESS('✅ Database seeded successfully!')
        )

    def create_test_users(self):
        """Create test users for development"""
        users_data = [
            {
                'username': 'testuser1',
                'email': 'test1@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'password123'
            },
            {
                'username': 'testuser2',
                'email': 'test2@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'password': 'password123'
            },
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'password': 'admin123',
                'is_staff': True,
                'is_superuser': True
            }
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False)
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            else:
                self.stdout.write(f'User already exists: {user.username}')

    def create_shopping_data(self):
        """Create sample shopping lists and items"""
        users = User.objects.all()

        if not users.exists():
            return

        # Create shopping lists
        list_names = [
            'Weekly Groceries',
            'Dinner Party',
            'Healthy Snacks',
            'Breakfast Items',
            'Emergency Supplies'
        ]

        for i, list_name in enumerate(list_names):
            user = users[i % users.count()]
            shopping_list, created = ShoppingList.objects.get_or_create(
                name=list_name,
                creator=user,
                defaults={
                    'is_collaborative': i % 2 == 0  # Alternate between collaborative and private
                }
            )

            if created:
                # Add sample items
                sample_items = [
                    'Milk', 'Bread', 'Eggs', 'Cheese', 'Tomatoes',
                    'Onions', 'Chicken', 'Rice', 'Pasta', 'Apples',
                    'Bananas', 'Yogurt', 'Butter', 'Olive Oil', 'Salt'
                ]

                for item_name in random.sample(sample_items, random.randint(3, 8)):
                    ShoppingItem.objects.create(
                        shopping_list=shopping_list,
                        added_by=user,
                        name=item_name,
                        quantity=random.randint(1, 5),
                        unit=random.choice(
                            ['kg', 'pieces', 'liters', 'packages']),
                        is_completed=random.choice([True, False])
                    )

                self.stdout.write(f'Created shopping list: {list_name}')
