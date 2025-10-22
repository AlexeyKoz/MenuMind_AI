# Inventory Agent Technical Brief
**Date**: October 22, 2025  
**Purpose**: Integration Analysis for 6-Sprint Multilingual Translation & Validation System  
**Status**: Current Implementation Analysis Complete

---

## 1. Architecture Overview

### High-Level Summary
The **Inventory Agent** is a standalone AI-powered feature that generates recipe suggestions from users' current inventory items. It operates **independently** of the main Recipe system and does NOT currently integrate with the 6-sprint translation/validation system.

### File Structure
```
backend/apps/shopping/
├── models.py                  # Inventory, InventoryHistory models
├── inventory_services.py      # InventoryRecipeGenerator (Groq-based AI)
├── inventory_views.py         # InventoryViewSet with generate_recipes endpoint
├── serializers.py             # RecipeFromInventorySerializer
└── urls.py                    # API routing

frontend/src/pages/
└── Inventory.tsx              # Complete frontend UI with caching logic
```

**Key Insight**: The Inventory Agent is **separate** from the main recipe system (`apps/recipes/`). It has its own:
- AI generation service (`InventoryRecipeGenerator`)
- Data models (`Inventory`, `InventoryHistory`)
- API endpoints (under `/api/inventory/`)
- Frontend caching (localStorage, 24-hour TTL)

---

## 2. Current Workflow

### Step-by-Step Flow

```
User opens Inventory page
    ↓
Frontend loads inventory items (grouped by location)
    ↓
User clicks "Get Recipe Suggestions" button
    ↓
[FRONTEND CACHE CHECK - localStorage]
    ├─ Cache exists + inventory unchanged → Show cached recipes instantly ⚡
    └─ No cache OR inventory changed → Continue to API call
    ↓
POST /api/inventory/generate_recipes/
    ↓
[BACKEND: InventoryRecipeGenerator]
    ↓
Generate prompt with inventory data + user profile
    ↓
Call Groq API (llama-3.1-8b-instant)
    ↓
Receive JSON array of recipe briefs (5 max)
    ↓
Return to frontend
    ↓
[FRONTEND: Cache Management]
    ↓
Save to localStorage with:
    - recipes: array of brief recipes
    - inventoryHash: hash of current inventory state
    - timestamp: generation time
    ↓
Add to recipeHistory (max 10 generations)
    ↓
Display in modal
    ↓
User can:
    ├─ Browse history (Previous/Next buttons)
    ├─ Generate new (force regeneration)
    └─ Click "Create Recipe" → Call RecipeAgent (different system!)
```

### Cache Invalidation Triggers
1. **Inventory changed** (add/edit/delete item) → Clear cache
2. **24-hour expiration** → Auto-cleared on page load
3. **User creates full recipe** → Clear cache (items "consumed")
4. **User clicks "Generate New"** → Force regeneration

---

## 3. Database Schema

### Inventory Model (`apps/shopping/models.py`)
```python
class Inventory(models.Model):
    id = UUIDField(primary_key=True)
    user = ForeignKey(User)
    
    # Item details
    name = CharField(max_length=200)
    quantity = DecimalField(max_digits=10, decimal_places=2)
    unit = CharField(max_length=20, default='unit')
    category = CharField(choices=CATEGORIES)
    
    # Storage & expiration
    expiration_date = DateField(null=True, blank=True)
    purchase_date = DateField(auto_now_add=True)
    location = CharField(choices=['fridge', 'freezer', 'pantry', 'counter'])
    
    # IML Integration (Sprint 1 compatible!)
    ingredient_key = CharField(max_length=200, null=True, db_index=True)
    unit_type = CharField(choices=['weight', 'volume', 'count', 'cooking'])
    expiration_source = CharField(choices=['iml', 'ai', 'manual'])
    
    # Metadata
    nutrition_data = JSONField(default=dict)
    barcode = CharField(max_length=50, blank=True)
    notes = TextField(blank=True)
    
    # Permissions (inherited from shopping list)
    shopping_list = ForeignKey('ShoppingList', null=True)
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**Key Observations**:
- ✅ Already has `ingredient_key` field → **Ready for IML integration!**
- ✅ Has `unit_type` → Can use IMLService for validation
- ❌ No `RecipeBrief` model → Recipes stored only in frontend localStorage
- ❌ No database persistence for generated recipe briefs

### InventoryHistory Model
```python
class InventoryHistory(models.Model):
    id = UUIDField(primary_key=True)
    inventory_item = ForeignKey(Inventory)
    action = CharField(choices=['added', 'consumed', 'expired', 'moved', 'adjusted', 'deleted'])
    
    quantity_change = DecimalField  # +/-
    previous_quantity = DecimalField
    new_quantity = DecimalField
    
    # Optional recipe linkage
    recipe = ForeignKey('recipes.Recipe', null=True)  # ← Could link to canonical recipes!
    notes = TextField(blank=True)
    timestamp = DateTimeField(auto_now_add=True)
```

**Key Observations**:
- ✅ Can track recipe consumption
- ✅ Has foreign key to `recipes.Recipe` → Can integrate with canonical recipes
- ❌ Currently not used for recipe tracking

---

## 4. API Endpoints

### 4.1 Generate Recipe Suggestions
**Endpoint**: `POST /api/inventory/generate_recipes/`  
**File**: `backend/apps/shopping/inventory_views.py:515-573`

**Request Body** (optional):
```json
{
    "max_recipes": 5,
    "prioritize_expiring": true,
    "max_missing_ingredients": 2
}
```

**Response**:
```json
{
    "success": true,
    "inventory_count": 15,
    "recipe_count": 5,
    "recipes": [
        {
            "name": "Quick Tomato Pasta",
            "priority": "urgent",  // urgent | high | normal
            "ingredients_from_inventory": [
                {"name": "tomatoes", "quantity": 200, "unit": "g"},
                {"name": "pasta", "quantity": 300, "unit": "g"}
            ],
            "missing_ingredients": ["olive oil", "garlic"],
            "nutrition": {
                "calories": 450,
                "protein": 12,
                "carbs": 75,
                "fat": 8
            },
            "difficulty": "easy",  // easy | intermediate | advanced
            "cooking_time": "20 min",
            "reasoning": "Uses tomatoes expiring in 2 days and available pasta"
        }
    ]
}
```

**Current Implementation**:
```python
@action(detail=False, methods=['post'])
def generate_recipes(self, request):
    # 1. Get user's inventory
    inventory_items = self.get_queryset()
    
    # 2. Format for AI
    items_data = [{
        'name': item.name,
        'quantity': float(item.quantity),
        'unit': item.unit,
        'expiration_date': item.expiration_date.isoformat() if item.expiration_date else None,
        'location': item.location,
        'category': item.category
    } for item in inventory_items]
    
    # 3. Get user profile
    user_profile = {
        'daily_calories_goal': getattr(request.user, 'daily_calories_goal', 2000),
        'daily_protein_goal': getattr(request.user, 'daily_protein_goal', 150),
        'dietary_restrictions': [],  # TODO: Add to user model
        'allergies': [],  # TODO: Add to user model
        'activity_level': 'moderate'
    }
    
    # 4. Generate with AI
    generator = InventoryRecipeGenerator()
    recipes = generator.generate_recipes(
        inventory_items=items_data,
        user_profile=user_profile,
        max_recipes=request.data.get('max_recipes', 5),
        prioritize_expiring=request.data.get('prioritize_expiring', True),
        max_missing_ingredients=request.data.get('max_missing_ingredients', 2)
    )
    
    # 5. Return serialized recipes
    serializer = RecipeFromInventorySerializer(recipes, many=True)
    return Response({...})
```

### 4.2 Other Inventory Endpoints
- `GET /api/inventory/` → List all inventory items
- `POST /api/inventory/` → Add item
- `PUT /api/inventory/{id}/` → Update item
- `DELETE /api/inventory/{id}/` → Delete item
- `GET /api/inventory/by-location/` → Group by location (used by frontend)

---

## 5. Caching Strategy

### Current Implementation: Frontend localStorage (24-hour TTL)

**File**: `frontend/src/pages/Inventory.tsx:40-122`

```typescript
// Cache structure in localStorage
interface RecipeHistoryEntry {
    recipes: RecipeSuggestion[];
    inventoryHash: string;
    timestamp: Date;
}

// Storage key
const STORAGE_KEY = 'inventory_recipe_history';
const MAX_STORAGE_AGE_HOURS = 24;

// Save to localStorage
const saveRecipeHistoryToStorage = (history: RecipeHistoryEntry[]) => {
    try {
        const serialized = JSON.stringify({
            version: 1,
            entries: history.map(entry => ({
                recipes: entry.recipes,
                inventoryHash: entry.inventoryHash,
                timestamp: entry.timestamp.toISOString()
            }))
        });
        localStorage.setItem(STORAGE_KEY, serialized);
    } catch (error) {
        console.error('[STORAGE] Failed to save:', error);
    }
};

// Load from localStorage
const loadRecipeHistoryFromStorage = (): RecipeHistoryEntry[] => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return [];
        
        const parsed = JSON.parse(stored);
        if (parsed.version !== 1) return [];
        
        // Check age
        const oldestTimestamp = new Date(parsed.entries[0]?.timestamp);
        const ageHours = (Date.now() - oldestTimestamp.getTime()) / (1000 * 60 * 60);
        
        if (ageHours > MAX_STORAGE_AGE_HOURS) {
            // Expired, clear storage
            clearRecipeHistoryFromStorage();
            return [];
        }
        
        // Restore
        return parsed.entries.map(entry => ({
            recipes: entry.recipes,
            inventoryHash: entry.inventoryHash,
            timestamp: new Date(entry.timestamp)
        }));
    } catch (error) {
        return [];
    }
};
```

**Cache Invalidation Logic**:
```typescript
const generateInventoryHash = (inventoryData: LocationGroup): string => {
    // Create hash from all items
    const sortedItems = allItems.sort((a, b) => a.id.localeCompare(b.id));
    const hashString = sortedItems.map(item =>
        `${item.name}-${item.quantity}-${item.unit}-${item.expiration_date || ''}`
    ).join('|');
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < hashString.length; i++) {
        hash = ((hash << 5) - hash) + hashString.charCodeAt(i);
    }
    return Math.abs(hash).toString(36);
};

// On inventory load
const currentHash = generateInventoryHash(data);
if (currentHash !== lastInventoryHash && recipeHistory.length > 0) {
    // Inventory changed → Clear cache
    setRecipeHistory([]);
    clearRecipeHistoryFromStorage();
}
```

**Cache Hit Logic**:
```typescript
const handleGenerateRecipes = async (forceRegenerate: boolean = false) => {
    const currentHash = generateInventoryHash(locationData);
    const isCacheValid = cachedRecipes.length > 0 && cachedRecipesHash === currentHash;
    
    if (isCacheValid && !forceRegenerate) {
        // Cache HIT → Show instantly
        setRecipes(cachedRecipes);
        setShowRecipesModal(true);
        toast.success('Showing cached recipes ⚡');
        return;
    }
    
    // Cache MISS → Call API
    setGeneratingRecipes(true);
    try {
        const response = await api.generateRecipesFromInventory({...});
        
        // Save to cache
        const newEntry = {
            recipes: response.recipes,
            inventoryHash: currentHash,
            timestamp: new Date()
        };
        
        const updatedHistory = [...recipeHistory, newEntry].slice(-10); // Keep last 10
        setRecipeHistory(updatedHistory);
        setCurrentHistoryIndex(updatedHistory.length - 1);
        
        setRecipes(response.recipes);
        setShowRecipesModal(true);
    } finally {
        setGeneratingRecipes(false);
    }
};
```

**Current Cache Issues**:
- ❌ No backend caching (every page refresh = new API call if cache expired)
- ❌ Not shared across devices/sessions
- ❌ Lost on browser clear/incognito mode
- ❌ No integration with Redis or PostgreSQL

---

## 6. AI Integration

### 6.1 AI Provider
**Current**: Groq (llama-3.1-8b-instant)  
**File**: `backend/apps/shopping/inventory_services.py:409-426`

```python
class InventoryRecipeGenerator:
    def __init__(self):
        from groq import Groq
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            self.groq_client = Groq(api_key=groq_api_key)
            self.model = "llama-3.1-8b-instant"  # Fast, lower quality
        else:
            self.groq_client = None
```

**Why llama-3.1-8b-instant?**
- ✅ Fast response (~2-3s)
- ✅ Free tier: 30 requests/min
- ❌ Lower quality than 70B models
- ❌ Less accurate ingredient parsing
- ❌ Prone to JSON errors (has fallback)

### 6.2 Generation Prompts

**Brief Recipe Generation** (`inventory_services.py:470-516`):
```python
prompt = f"""You are a recipe recommendation AI for MenuMine.

Current Inventory:
{inventory_summary}

User Profile:
{user_summary}

Task: Generate {max_recipes} recipe suggestions that:
1. PRIORITIZE items expiring within 3 days (mark priority as "urgent")
2. Use available ingredients (minimize missing items, max {max_missing_ingredients})
3. Fit user's nutrition goals
4. Match user preferences
5. Are realistic and achievable

For each recipe, provide:
- name: Recipe name
- priority: "urgent" (uses expiring items), "high" (uses most inventory), or "normal"
- ingredients_from_inventory: List of {{name, quantity, unit}}
- missing_ingredients: List of ingredient names (max {max_missing_ingredients})
- nutrition: {{calories, protein, carbs, fat}}
- difficulty: "easy", "intermediate", or "advanced"
- cooking_time: e.g., "20 min", "45 min"
- reasoning: Why this recipe

Return ONLY valid JSON array (no markdown):
[
  {{
    "name": "...",
    "priority": "urgent|high|normal",
    "ingredients_from_inventory": [
      {{"name": "...", "quantity": X, "unit": "..."}},
      ...
    ],
    ...
  }}
]"""
```

**System Message**:
```python
{
    "role": "system",
    "content": "You are a professional chef and nutritionist. Return ONLY valid JSON array."
}
```

**Temperature**: 0.7 (moderate creativity)  
**Max Tokens**: 2000

### 6.3 Error Handling & Fallback
```python
try:
    response = self.groq_client.chat.completions.create(...)
    response_text = completion.choices[0].message.content.strip()
    
    # Clean markdown code blocks
    if response_text.startswith('```'):
        response_text = response_text.split('```')[1]
        if response_text.startswith('json'):
            response_text = response_text[4:]
    
    recipes = json.loads(response_text)
    return recipes[:max_recipes]
    
except json.JSONDecodeError as e:
    # Fallback: Template-based recipes
    return self._generate_fallback_recipes(inventory_items, max_recipes)
    
except Exception as e:
    # Fallback: Template-based recipes
    return self._generate_fallback_recipes(inventory_items, max_recipes)
```

**Fallback Logic** (`_generate_fallback_recipes`):
- Groups ingredients by category
- Returns hardcoded templates like:
  - "Quick Stir-Fry" (if vegetables available)
  - "Simple Pasta" (if pasta + sauce ingredients)
  - "Breakfast Bowl" (if eggs + pantry items)

---

## 7. Integration Gaps with 6-Sprint System

### ❌ NOT USING:

1. **Sprint 2: IMLService** (In-Memory Caching)
   - Inventory model HAS `ingredient_key` field
   - But NOT populated or used
   - Could use IMLService to:
     - Normalize ingredient names
     - Validate quantities
     - Get multilingual names

2. **Sprint 3: UniversalValidator**
   - NO validation of generated recipes
   - Cannot detect:
     - Invalid ingredient amounts
     - Missing critical steps
     - Dangerous cooking instructions
     - Ingredient incompatibilities

3. **Sprint 4: SmartTranslationService**
   - NO translation support
   - Recipes generated in **English only**
   - Cannot generate recipes in user's language
   - Cannot translate inventory item names

4. **Sprint 5: DiscoveryCache**
   - NO backend caching
   - Every API call = full Groq generation
   - Cannot share cache across users/devices

5. **Sprint 6: UniversalAgentAPI**
   - Inventory Agent is **completely separate**
   - Does NOT use `submit_recipe()` API
   - Generated briefs are NOT saved to `CanonicalRecipe`
   - No RCIP 2.0 format compliance

### ✅ READY FOR INTEGRATION:

1. **Database Schema**:
   - `Inventory.ingredient_key` → Can link to IML
   - `Inventory.unit_type` → Ready for validation
   - `InventoryHistory.recipe` → Can link to canonical recipes

2. **API Structure**:
   - Clean ViewSet architecture
   - Easy to add validation/translation layers
   - Can return RCIP 2.0 format

3. **Frontend Caching**:
   - Well-designed localStorage system
   - Can be adapted to use Redis cache
   - History navigation UX is excellent

---

## 8. Code Snippets

### 8.1 Current Recipe Generation
```python
# File: backend/apps/shopping/inventory_services.py:427-578

class InventoryRecipeGenerator:
    def generate_recipes(self, inventory_items, user_profile, max_recipes=5, 
                        prioritize_expiring=True, max_missing_ingredients=2):
        if not self.groq_client:
            return []
        
        # Sort by expiration if prioritizing
        if prioritize_expiring:
            inventory_items = sorted(inventory_items,
                key=lambda x: x.get('expiration_date') or '9999-12-31')
        
        # Build prompt
        inventory_summary = self._build_inventory_summary(inventory_items)
        user_summary = self._build_user_summary(user_profile)
        
        prompt = f"""..."""  # See section 6.2
        
        # Call Groq
        completion = self.groq_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "..."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse response
        response_text = completion.choices[0].message.content.strip()
        recipes = json.loads(response_text)
        return recipes[:max_recipes]
```

### 8.2 Frontend Cache Check
```typescript
// File: frontend/src/pages/Inventory.tsx:302-350

const handleGenerateRecipes = async (forceRegenerate: boolean = false) => {
    const currentHash = generateInventoryHash(locationData);
    const isCacheValid = cachedRecipes.length > 0 && cachedRecipesHash === currentHash;
    
    if (isCacheValid && !forceRegenerate) {
        // ⚡ Cache HIT - Show instantly
        console.log('[RECIPES] ✅ Using cached recipes');
        setRecipes(cachedRecipes);
        setShowRecipesModal(true);
        toast.success('Showing cached recipes ⚡');
        return;
    }
    
    // Cache MISS - Generate new
    console.log('[RECIPES] ❌ Cache miss, generating new recipes');
    setGeneratingRecipes(true);
    
    try {
        const response = await api.generateRecipesFromInventory({
            max_recipes: 5,
            prioritize_expiring: true,
            max_missing_ingredients: 2
        });
        
        // Save to cache
        const newEntry = {
            recipes: response.recipes,
            inventoryHash: currentHash,
            timestamp: new Date()
        };
        
        const updatedHistory = [...recipeHistory, newEntry].slice(-10);
        setRecipeHistory(updatedHistory);
        setCurrentHistoryIndex(updatedHistory.length - 1);
        
        setRecipes(response.recipes);
        setShowRecipesModal(true);
        toast.success(`Generated ${response.recipes.length} recipe suggestions!`);
    } finally {
        setGeneratingRecipes(false);
    }
};
```

### 8.3 User Clicks "Create Recipe" (Different System!)
```typescript
// File: frontend/src/pages/Inventory.tsx:352-450

const handleRecipeClick = async (recipe: RecipeSuggestion) => {
    // This calls RecipeAgentService, NOT InventoryRecipeGenerator!
    setCreatingRecipe(recipe.name);
    
    try {
        const response = await fetch('/api/ai-agents/generate-recipes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                query: recipe.name,
                max_recipes: 1
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            toast.success('Recipe created! Check "My Recipes"');
            
            // Clear recipe suggestions cache (inventory "used")
            setRecipeHistory([]);
            setCurrentHistoryIndex(-1);
            clearRecipeHistoryFromStorage();
            
            // Navigate to My Recipes
            window.location.href = '/recipes';
        }
    } finally {
        setCreatingRecipe(null);
    }
};
```

**IMPORTANT**: When user clicks "Create Recipe", it:
1. Calls **different API**: `/api/ai-agents/generate-recipes/`
2. Uses **different service**: `RecipeAgentService` (not `InventoryRecipeGenerator`)
3. Uses **different AI**: Groq Llama 3.1 70B (not 8B instant)
4. Generates **full recipe** with steps, not just brief
5. Saves to **CanonicalRecipe** model
6. Navigates to **My Recipes** page

This is a **critical integration point**!

---

## 9. Recommendations for Integration

### Phase 1: Validation (Sprint 3 Integration)

**Goal**: Validate inventory recipes before showing to user

```python
# File: backend/apps/shopping/inventory_views.py

from apps.core.services import get_universal_validator

@action(detail=False, methods=['post'])
def generate_recipes(self, request):
    # ... existing code ...
    
    recipes = generator.generate_recipes(...)
    
    # NEW: Validate each recipe
    validator = get_universal_validator()
    validated_recipes = []
    
    for recipe in recipes:
        # Convert to canonical format
        canonical_data = {
            'name': recipe['name'],
            'ingredients': [
                {
                    'iml_key': ing['name'].lower().replace(' ', '-'),  # TODO: Use IML lookup
                    'amount': ing['quantity'],
                    'unit': ing['unit']
                }
                for ing in recipe['ingredients_from_inventory']
            ],
            'steps': [],  # Brief recipes don't have steps yet
            'metadata': {
                'difficulty': recipe['difficulty'],
                'cook_time': recipe['cooking_time'],
                'nutrition': recipe['nutrition']
            }
        }
        
        # Validate
        result = validator.validate_recipe(canonical_data)
        
        if result.is_valid or result.overall_score >= 70:
            recipe['validation_score'] = result.overall_score
            recipe['validation_issues'] = [i.message for i in result.issues]
            validated_recipes.append(recipe)
        else:
            logger.warning(f"Recipe '{recipe['name']}' failed validation: {result.issues}")
    
    return Response({
        'success': True,
        'recipe_count': len(validated_recipes),
        'recipes': validated_recipes
    })
```

### Phase 2: Translation (Sprint 4 Integration)

**Goal**: Generate recipes in user's language

```python
# File: backend/apps/shopping/inventory_services.py

from apps.core.services import get_iml_service, get_smart_translation_service

class InventoryRecipeGenerator:
    def __init__(self):
        self.groq_client = Groq(api_key=...)
        self.iml_service = get_iml_service()
        self.translator = get_smart_translation_service()
    
    def generate_recipes(self, inventory_items, user_profile, max_recipes=5,
                        target_language='en', **kwargs):
        # 1. Translate inventory items to English (canonical)
        translated_inventory = []
        for item in inventory_items:
            if target_language != 'en':
                # Use IML to get English name
                eng_name = self.iml_service.reverse_translate(
                    item['name'], source_lang=target_language
                )
                item['canonical_name'] = eng_name or item['name']
            else:
                item['canonical_name'] = item['name']
            
            translated_inventory.append(item)
        
        # 2. Generate recipes in English (canonical)
        recipes = self._generate_with_groq(translated_inventory, user_profile, max_recipes)
        
        # 3. Translate recipes to target language
        if target_language != 'en':
            for recipe in recipes:
                # Translate recipe name
                recipe['name'] = self.translator.translate_text(
                    recipe['name'], target_lang=target_language
                )
                
                # Translate ingredients
                for ing in recipe['ingredients_from_inventory']:
                    ing['name'] = self.iml_service.translate_ingredient(
                        ing['canonical_name'], target_lang=target_language
                    )
        
        return recipes
```

### Phase 3: Backend Caching (Sprint 5 Integration)

**Goal**: Cache recipe briefs in Redis/PostgreSQL

```python
# File: backend/apps/shopping/models.py

class InventoryRecipeBrief(models.Model):
    """Cache for AI-generated recipe briefs from inventory"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Inventory snapshot
    inventory_hash = models.CharField(max_length=100, db_index=True)
    inventory_snapshot = models.JSONField()  # Items at generation time
    
    # Generated recipes
    recipes = models.JSONField()  # Array of brief recipes
    
    # Metadata
    generation_params = models.JSONField()  # max_recipes, prioritize_expiring, etc.
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 24-hour TTL
    
    # AI info
    ai_model = models.CharField(max_length=50, default='groq-llama-3.1-8b')
    generation_time_ms = models.IntegerField()
    
    class Meta:
        db_table = 'inventory_recipe_briefs'
        indexes = [
            models.Index(fields=['user', 'inventory_hash']),
            models.Index(fields=['expires_at']),
        ]

# File: backend/apps/shopping/inventory_views.py

from django.core.cache import cache
from datetime import timedelta

@action(detail=False, methods=['post'])
def generate_recipes(self, request):
    # 1. Calculate inventory hash
    inventory_items = self.get_queryset()
    inventory_hash = self._hash_inventory(inventory_items)
    
    # 2. Check Redis cache
    cache_key = f'inventory_recipes:{request.user.id}:{inventory_hash}'
    cached = cache.get(cache_key)
    if cached:
        return Response({
            'success': True,
            'cached': True,
            'recipes': cached['recipes']
        })
    
    # 3. Check PostgreSQL cache
    db_cached = InventoryRecipeBrief.objects.filter(
        user=request.user,
        inventory_hash=inventory_hash,
        expires_at__gt=timezone.now()
    ).first()
    
    if db_cached:
        # Update Redis
        cache.set(cache_key, db_cached.recipes, timeout=3600)
        return Response({
            'success': True,
            'cached': True,
            'recipes': db_cached.recipes
        })
    
    # 4. Generate new recipes
    generator = InventoryRecipeGenerator()
    recipes = generator.generate_recipes(...)
    
    # 5. Save to PostgreSQL
    InventoryRecipeBrief.objects.create(
        user=request.user,
        inventory_hash=inventory_hash,
        inventory_snapshot=items_data,
        recipes=recipes,
        generation_params={...},
        expires_at=timezone.now() + timedelta(hours=24),
        generation_time_ms=...
    )
    
    # 6. Save to Redis
    cache.set(cache_key, recipes, timeout=3600)
    
    return Response({
        'success': True,
        'cached': False,
        'recipes': recipes
    })
```

### Phase 4: Universal Agent API (Sprint 6 Integration)

**Goal**: Use UniversalAgentAPI when user clicks "Create Recipe"

```python
# File: backend/apps/shopping/inventory_views.py

from apps.core.services import get_universal_agent_service

@action(detail=False, methods=['post'])
def create_full_recipe_from_brief(self, request):
    """
    Convert a recipe brief to a full canonical recipe
    
    POST /api/inventory/create-recipe/
    Body:
    {
        "recipe_brief": {
            "name": "Quick Tomato Pasta",
            "ingredients_from_inventory": [...],
            "missing_ingredients": [...],
            ...
        }
    }
    """
    recipe_brief = request.data.get('recipe_brief')
    
    # 1. Build RCIP 2.0 structure from brief
    rcip_data = {
        'metadata': {
            'title': recipe_brief['name'],
            'source_language': request.user.preferred_language or 'en',
            'servings': 2,
            'tags': [recipe_brief.get('difficulty', 'easy')]
        },
        'structure': {
            'ingredients': [
                {
                    'iml_key': ing['name'].lower().replace(' ', '-'),
                    'amount': ing['quantity'],
                    'unit': ing['unit']
                }
                for ing in recipe_brief['ingredients_from_inventory']
            ],
            'steps': []  # Will be generated by agent
        }
    }
    
    # 2. Submit to Universal Agent API
    agent = get_universal_agent_service()
    result = agent.submit_recipe(
        recipe_data=rcip_data,
        agent_name='inventory-agent',
        skip_validation=False,  # Validate!
        auto_translate=True,    # Translate to all languages
        auto_cache=True         # Update discovery cache
    )
    
    if not result['success']:
        return Response({
            'error': 'Recipe validation failed',
            'validation': result['validation']
        }, status=400)
    
    # 3. Track consumption in InventoryHistory
    for ing in recipe_brief['ingredients_from_inventory']:
        inventory_item = Inventory.objects.filter(
            user=request.user,
            name__iexact=ing['name']
        ).first()
        
        if inventory_item:
            InventoryHistory.objects.create(
                inventory_item=inventory_item,
                action='consumed',
                quantity_change=-ing['quantity'],
                previous_quantity=inventory_item.quantity,
                new_quantity=inventory_item.quantity - ing['quantity'],
                recipe_id=result['recipe_id']
            )
    
    return Response({
        'success': True,
        'recipe_id': result['recipe_id'],
        'validation': result['validation'],
        'translations_queued': result['translations_queued']
    })
```

---

## 10. Summary & Integration Priority

### Current State
- ✅ **Functional**: Works well for English-only, single-device use
- ✅ **Fast**: llama-3.1-8b-instant generates in ~2-3s
- ✅ **Smart**: Prioritizes expiring items, respects user preferences
- ✅ **Cached**: localStorage prevents redundant API calls
- ❌ **Isolated**: No integration with main recipe system
- ❌ **English-only**: No multilingual support
- ❌ **Unvalidated**: No recipe quality checks
- ❌ **Ephemeral**: Cache lost on browser clear

### Integration Priority (Recommended Order)

#### 🔥 **Priority 1: Phase 4 (Universal Agent API)**
**Why first**: When user clicks "Create Recipe", they expect it in their recipe library with full translation support.

**Benefit**: 
- Recipes appear in "My Recipes" in user's language
- Automatic translation to all 3 languages
- Validation before saving
- Proper RCIP 2.0 format

**Effort**: Medium (3-4 hours)

---

#### 🟡 **Priority 2: Phase 1 (Validation)**
**Why second**: Prevent showing invalid/dangerous recipes to users.

**Benefit**:
- Filter out recipes with invalid ingredient amounts
- Detect missing critical steps
- Show validation score to user
- Build trust in AI suggestions

**Effort**: Low (2 hours)

---

#### 🟢 **Priority 3: Phase 2 (Translation)**
**Why third**: Once recipes can be saved properly (Phase 4), add multilingual brief generation.

**Benefit**:
- Generate recipe briefs in user's language
- Translate inventory item names for better AI understanding
- Consistent with main recipe system

**Effort**: Medium (4-5 hours)

---

#### 🔵 **Priority 4: Phase 3 (Backend Caching)**
**Why last**: Optimization after core functionality is integrated.

**Benefit**:
- Cache persists across devices
- Faster load times (Redis)
- Reduce Groq API calls

**Effort**: Medium (3-4 hours)

---

### Total Integration Effort
- **Phase 1**: 2 hours
- **Phase 2**: 4-5 hours
- **Phase 3**: 3-4 hours
- **Phase 4**: 3-4 hours

**Total**: ~12-15 hours for complete integration

### Expected Results After Integration
1. ✅ Inventory recipes validated before showing
2. ✅ Recipe briefs generated in user's language
3. ✅ Full recipes saved to canonical library with translations
4. ✅ Backend caching reduces API costs
5. ✅ Seamless UX across Inventory → Recipe Library
6. ✅ RCIP 2.0 compliance for all inventory-generated recipes

---

**END OF TECHNICAL BRIEF**

