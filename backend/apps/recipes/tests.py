from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Recipe, UserRecipe

User = get_user_model()


class RecipeModelTests(TestCase):
    """Tests for Recipe model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_recipe(self):
        """Test creating a recipe"""
        recipe = Recipe.objects.create(
            name="Test Recipe",
            description="A test recipe",
            ingredients=[
                {"name": "Flour", "amount": 2, "unit": "cups"},
                {"name": "Sugar", "amount": 1, "unit": "cup"}
            ],
            steps=[
                {"order": 1, "instruction": "Mix ingredients"},
                {"order": 2, "instruction": "Bake for 30 minutes"}
            ],
            created_by=self.user,
            servings=4,
            difficulty="beginner"
        )

        self.assertEqual(recipe.name, "Test Recipe")
        self.assertEqual(recipe.version, 1)
        self.assertTrue(recipe.is_latest_version)
        self.assertIsNotNone(recipe.recipe_hash)

    def test_recipe_hash_generation(self):
        """Test that recipe hash is generated automatically"""
        recipe = Recipe.objects.create(
            name="Chocolate Cake",
            ingredients=[
                {"name": "Chocolate", "amount": 200, "unit": "g"},
                {"name": "Flour", "amount": 2, "unit": "cups"}
            ],
            steps=[{"order": 1, "instruction": "Mix"}],
            created_by=self.user
        )

        self.assertIsNotNone(recipe.recipe_hash)
        self.assertEqual(len(recipe.recipe_hash), 64)  # SHA256 hash length

    def test_recipe_versioning(self):
        """Test that duplicate recipes create versions"""
        # Create first recipe
        recipe1 = Recipe.objects.create(
            name="Pasta Carbonara",
            ingredients=[
                {"name": "Pasta", "amount": 400, "unit": "g"},
                {"name": "Eggs", "amount": 4, "unit": "pieces"}
            ],
            steps=[{"order": 1, "instruction": "Cook pasta"}],
            created_by=self.user
        )

        # Create similar recipe (same name and ingredients)
        recipe2 = Recipe.objects.create(
            name="Pasta Carbonara",
            ingredients=[
                {"name": "Eggs", "amount": 4, "unit": "pieces"},
                {"name": "Pasta", "amount": 400, "unit": "g"}
            ],
            steps=[{"order": 1, "instruction": "Cook pasta differently"}],
            created_by=self.user
        )

        # Check versioning
        self.assertEqual(recipe1.version, 1)
        self.assertEqual(recipe2.version, 2)
        self.assertFalse(Recipe.objects.get(id=recipe1.id).is_latest_version)
        self.assertTrue(recipe2.is_latest_version)
        self.assertEqual(recipe2.parent_recipe, recipe1)

    def test_to_rcip_format(self):
        """Test RCIP format export"""
        recipe = Recipe.objects.create(
            name="Test RCIP Recipe",
            description="Testing RCIP format",
            ingredients=[{"name": "Salt", "amount": 1, "unit": "tsp"}],
            steps=[{"order": 1, "instruction": "Add salt"}],
            created_by=self.user,
            prep_time_minutes=5,
            cook_time_minutes=10,
            servings=2,
            difficulty="beginner",
            cuisine="Italian"
        )

        rcip_data = recipe.to_rcip_format()

        self.assertEqual(rcip_data['meta']['name'], "Test RCIP Recipe")
        self.assertEqual(rcip_data['meta']['servings']['amount'], 2)
        self.assertEqual(rcip_data['meta']['prep_time_minutes'], 5)
        self.assertEqual(rcip_data['meta']['cook_time_minutes'], 10)
        self.assertIn('Italian', rcip_data['meta']['keywords'])


class UserRecipeModelTests(TestCase):
    """Tests for UserRecipe model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            name="Test Recipe",
            ingredients=[{"name": "Flour", "amount": 2, "unit": "cups"}],
            steps=[{"order": 1, "instruction": "Mix"}],
            created_by=self.user
        )

    def test_save_recipe_to_user(self):
        """Test saving a recipe to user's collection"""
        user_recipe = UserRecipe.objects.create(
            user=self.user,
            recipe=self.recipe,
            notes="My favorite recipe",
            rating=5
        )

        self.assertEqual(user_recipe.user, self.user)
        self.assertEqual(user_recipe.recipe, self.recipe)
        self.assertEqual(user_recipe.rating, 5)
        self.assertEqual(user_recipe.times_cooked, 0)

    def test_unique_user_recipe(self):
        """Test that a user can't save the same recipe twice"""
        UserRecipe.objects.create(
            user=self.user,
            recipe=self.recipe
        )

        # Try to create duplicate
        with self.assertRaises(Exception):
            UserRecipe.objects.create(
                user=self.user,
                recipe=self.recipe
            )



