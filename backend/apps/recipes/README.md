# 🍳 Recipes App - RCIP Format Support

MenuMind AI's recipe management system with RCIP (Recipe Content Interchange Protocol) format support, automatic versioning, and deduplication.

## 📋 Features

### ✨ Core Features
- **RCIP Format Support** - Industry-standard recipe format
- **AI Recipe Search** - 🤖 Search web and automatically import recipes using AI
- **Automatic Deduplication** - Prevents duplicate recipes based on content hash
- **Version Control** - Track recipe modifications with automatic versioning
- **User Collections** - Save recipes, add notes, and rate them
- **Statistics Tracking** - Track how many times recipes are saved and cooked
- **Advanced Filtering** - Search by cuisine, difficulty, diet labels, and more

### 🎯 API Endpoints

#### **Recipes API** (`/api/recipes/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/recipes/recipes/` | GET | List all recipes (latest versions) |
| `/api/recipes/recipes/` | POST | Create a new recipe |
| `/api/recipes/recipes/{id}/` | GET | Get recipe details |
| `/api/recipes/recipes/{id}/` | PUT/PATCH | Update recipe |
| `/api/recipes/recipes/{id}/` | DELETE | Delete recipe |
| `/api/recipes/recipes/{id}/rcip_format/` | GET | Export recipe in RCIP format |
| `/api/recipes/recipes/{id}/versions/` | GET | Get all versions of a recipe |
| `/api/recipes/recipes/{id}/save_recipe/` | POST | Save recipe to user's collection |
| `/api/recipes/recipes/{id}/mark_cooked/` | POST | Mark recipe as cooked |
| `/api/recipes/recipes/my_recipes/` | GET | Get user's created recipes |
| `/api/recipes/recipes/popular/` | GET | Get popular recipes |
| `/api/recipes/recipes/ai_search/` | POST | 🤖 AI-powered recipe search and import |

#### **User Recipes API** (`/api/recipes/user-recipes/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/recipes/user-recipes/` | GET | List user's saved recipes |
| `/api/recipes/user-recipes/` | POST | Save a recipe |
| `/api/recipes/user-recipes/{id}/` | GET | Get saved recipe details |
| `/api/recipes/user-recipes/{id}/` | PUT/PATCH | Update notes/rating |
| `/api/recipes/user-recipes/{id}/` | DELETE | Remove from saved recipes |
| `/api/recipes/user-recipes/{id}/rate/` | POST | Rate a recipe |
| `/api/recipes/user-recipes/{id}/add_note/` | POST | Add/update notes |

### 🔍 Query Parameters

**List Recipes** (`GET /api/recipes/recipes/`)
- `difficulty` - Filter by difficulty (beginner, intermediate, advanced)
- `cuisine` - Filter by cuisine type
- `search` - Search by recipe name
- `diet` - Filter by diet label (vegetarian, vegan, gluten-free, etc.)

Example:
```
GET /api/recipes/recipes/?difficulty=beginner&cuisine=italian&search=pasta
```

## 📝 RCIP Format

The Recipe Content Interchange Protocol (RCIP) is used for standardized recipe data exchange.

### Example RCIP Format:

```json
{
  "rcip_version": "0.1",
  "id": "rcip-550e8400-e29b-41d4-a716-446655440000",
  "meta": {
    "name": "Spaghetti Carbonara",
    "description": "Classic Italian pasta dish",
    "author": "Chef Mario",
    "created_date": "2025-10-03T14:30:00Z",
    "source_url": "https://example.com/recipe",
    "difficulty": "intermediate",
    "servings": {
      "amount": 4,
      "unit": "portions",
      "adjustable": true
    },
    "prep_time_minutes": 10,
    "cook_time_minutes": 20,
    "total_time_minutes": 30,
    "keywords": ["Italian"],
    "diet_labels": ["vegetarian"]
  },
  "ingredients": [
    {
      "name": "Spaghetti",
      "amount": 400,
      "unit": "g",
      "category": "pasta"
    },
    {
      "name": "Eggs",
      "amount": 4,
      "unit": "pieces",
      "category": "dairy"
    }
  ],
  "steps": [
    {
      "order": 1,
      "instruction": "Boil water and cook spaghetti according to package directions"
    },
    {
      "order": 2,
      "instruction": "Beat eggs in a bowl and mix with grated cheese"
    }
  ],
  "extensions": {
    "version": 1,
    "times_cooked": 42,
    "parent_recipe_id": null
  }
}
```

## 🔐 Authentication

All recipe endpoints require JWT authentication. Include the access token in the request header:

```
Authorization: Bearer <your_jwt_token>
```

## 📚 Usage Examples

### Creating a Recipe

```bash
POST /api/recipes/recipes/
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Chocolate Chip Cookies",
  "description": "Soft and chewy cookies",
  "author": "Grandma",
  "ingredients": [
    {
      "name": "Flour",
      "amount": 2,
      "unit": "cups"
    },
    {
      "name": "Chocolate Chips",
      "amount": 1,
      "unit": "cup"
    }
  ],
  "steps": [
    {
      "order": 1,
      "instruction": "Preheat oven to 350°F"
    },
    {
      "order": 2,
      "instruction": "Mix all ingredients"
    }
  ],
  "prep_time_minutes": 15,
  "cook_time_minutes": 12,
  "servings": 24,
  "difficulty": "beginner",
  "diet_labels": ["vegetarian"]
}
```

### Saving a Recipe to Your Collection

```bash
POST /api/recipes/recipes/{recipe_id}/save_recipe/
Authorization: Bearer <token>

{
  "notes": "Reduce sugar by half",
  "rating": 5
}
```

### Marking a Recipe as Cooked

```bash
POST /api/recipes/recipes/{recipe_id}/mark_cooked/
Authorization: Bearer <token>
```

### Getting Popular Recipes

```bash
GET /api/recipes/recipes/popular/
Authorization: Bearer <token>
```

## 🔄 Versioning & Deduplication

The system automatically:
1. **Detects duplicates** based on recipe name and ingredients
2. **Creates versions** when similar recipes are added
3. **Links versions** via `parent_recipe` relationship
4. **Marks latest versions** with `is_latest_version=True`

When you create a recipe that's similar to an existing one, it becomes version 2, 3, etc.

## 📊 Models

### Recipe Model
- **RCIP metadata** - Version, name, description
- **Content** - Ingredients (JSON), steps (JSON)
- **Metadata** - Prep/cook time, servings, difficulty, cuisine, diet labels
- **Versioning** - Hash, version number, parent recipe reference
- **Statistics** - Times saved, times cooked

### UserRecipe Model
- **User data** - Notes, rating (1-5), times cooked by user
- **Tracking** - Saved at, last cooked timestamps

## 🎯 Admin Interface

Access the Django admin at `/admin/` to:
- Browse all recipes
- View recipe versions
- Check user saved recipes
- Monitor statistics

## 🔧 Development

### Run Tests
```bash
cd backend
python manage.py test apps.recipes
```

### Create Sample Data
```python
from apps.recipes.models import Recipe
from apps.users.models import User

user = User.objects.first()

recipe = Recipe.objects.create(
    name="Test Recipe",
    description="A test recipe",
    ingredients=[{"name": "Salt", "amount": 1, "unit": "tsp"}],
    steps=[{"order": 1, "instruction": "Add salt"}],
    created_by=user,
    servings=2,
    difficulty="beginner"
)
```

## 🚀 Future Enhancements

- [ ] AI recipe suggestions based on available ingredients
- [ ] Meal planning integration
- [ ] Recipe scaling (adjust servings)
- [ ] Nutrition information per serving
- [ ] Recipe sharing between users
- [ ] Recipe collections/cookbooks
- [ ] Photo upload support
- [ ] Recipe import from URLs
- [ ] Export to PDF

## 📖 References

- [RCIP Specification](https://github.com/openculinary/recipe-content-interchange-protocol)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [MenuMind AI Documentation](../../README.md)

