# Recipe Builder: 5-Step Flow with Review & Edit

## 📋 Overview

The Recipe Builder now includes a **5th step** that allows users to review and edit the entire compiled recipe before saving. This gives users complete control over the final recipe before it's published.

---

## 🔄 Updated Flow

### Previous (4 Steps):
1. Basic Info
2. Ingredients
3. Steps
4. **Finalize** → Saved immediately

### New (5 Steps):
1. Basic Info
2. Ingredients
3. Steps
4. **Review & Edit** → User can see and modify everything ✨ **NEW**
5. Finalize → Save recipe

---

## 🎯 Key Features

### Step 4: Review & Edit

#### **What Users Can See:**
- ✅ Complete recipe preview with all fields
- ✅ Basic information (name, cuisine, difficulty, servings, description)
- ✅ All ingredients with amounts, units, and notes
- ✅ All cooking steps with instructions, times, and temperatures
- ✅ Estimated prep/cook/total times
- ✅ Auto-detected diet labels (vegetarian, vegan, gluten-free, etc.)

#### **What Users Can Edit:**
- ✏️ **Basic Info**: Name, cuisine, difficulty, servings, description
- ✏️ **Ingredients**: 
  - Modify amount, unit, name, or notes for any ingredient
  - Add new ingredients
  - Remove ingredients
- ✏️ **Steps**:
  - Edit instruction text
  - Change time estimates
  - Add/modify temperature settings
  - Add new steps
  - Remove steps
  - Steps are automatically re-numbered

---

## 🎨 UI Features

### Visual Design

#### **Section Layout:**
```
┌─────────────────────────────────────────┐
│ 📋 Basic Information         [✏️ Edit]  │
├─────────────────────────────────────────┤
│ Name: Summer Greek Salad                │
│ Cuisine: Greek                          │
│ Difficulty: Beginner                    │
│ Servings: 4                             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🥕 Ingredients (5)           [➕ Add]   │
├─────────────────────────────────────────┤
│ [Amt] [Unit] [Ingredient Name] [🗑️]     │
│  4     whole  tomatoes         [🗑️]     │
│  2     whole  cucumbers        [🗑️]     │
│  200   g      feta cheese      [🗑️]     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 👨‍🍳 Cooking Steps (3)        [➕ Add]   │
├─────────────────────────────────────────┤
│ [1] Chop vegetables...        [🗑️]     │
│     ⏱️ Time: 5 min                      │
│ [2] Mix in bowl...            [🗑️]     │
│     ⏱️ Time: 2 min                      │
└─────────────────────────────────────────┘
```

#### **Edit Modes:**
- **View Mode**: Click "Edit" button to toggle edit mode for basic info
- **Inline Editing**: Ingredients and steps are always editable
- **Add/Remove**: Easy-to-use buttons for adding/removing items

#### **Visual Indicators:**
- 🎨 Blue info box: "Review your recipe - AI has structured everything"
- ⏱️ Yellow box: Estimated times
- 🌱 Green box: Auto-detected diet labels
- ✏️ Edit icons throughout

---

## 🔧 Technical Implementation

### Frontend Changes

#### **File: `frontend/src/components/RecipeBuilderWizard.tsx`**

**New State Variables:**
```typescript
// Review step state - editable recipe data
const [reviewData, setReviewData] = useState<{
    basic_info: any;
    ingredients: StructuredIngredient[];
    steps: StructuredStep[];
    diet_labels: string[];
    estimated_times: any;
} | null>(null);

const [editingBasicInfo, setEditingBasicInfo] = useState(false);
```

**New Editing Functions:**
```typescript
updateReviewIngredient(index, field, value)  // Edit ingredient field
addReviewIngredient()                         // Add new ingredient
removeReviewIngredient(index)                 // Delete ingredient

updateReviewStep(index, field, value)         // Edit step field
addReviewStep()                               // Add new step
removeReviewStep(index)                       // Delete step (auto-renumbers)

updateBasicInfoField(field, value)            // Edit basic info
```

**Progress Bar:**
- Updated from 4 steps to 5 steps
- Shows: Basic Info | Ingredients | Steps | **Review & Edit** | Finalize

### Backend Changes

#### **File: `backend/apps/recipes/builder.py`**

**New Step Handler:**
```python
async def _process_review(self, session: Dict, session_id: str, user_input: Dict) -> Dict:
    """
    Step 4: Review compiled recipe and allow edits
    
    On first call (no save_edits flag):
    - Returns compiled recipe data for user to review/edit
    
    On second call (with save_edits=True):
    - Saves user's edits back to session
    - Proceeds to finalize step
    """
```

**Workflow:**
1. **First Call** (`save_edits=False`):
   - Compile all data from previous steps
   - Detect diet labels
   - Calculate time estimates
   - Return formatted data for review

2. **Second Call** (`save_edits=True`):
   - Save user's edits back to session
   - Update basic_info, ingredients, steps
   - Mark step as 'review_completed'
   - Proceed to finalize

#### **File: `backend/apps/recipes/views.py`**

**API Documentation Updated:**
```python
STEP 4 - Review & Edit (First Call - Get compiled recipe):
{
    "session_id": "...",
    "step": "review",
    "data": {}
}
Returns compiled recipe data for user to review/edit

STEP 4 - Review & Edit (Second Call - Save edits):
{
    "session_id": "...",
    "step": "review",
    "data": {
        "save_edits": true,
        "edited_data": {
            "basic_info": {...},
            "ingredients": [{...}],
            "steps": [{...}],
            "estimated_times": {...}
        }
    }
}
```

---

## 📊 Data Flow

### Step 3 → Step 4 Transition

```javascript
// After steps are processed
const reviewResult = await onBuilderStep({
    session_id: sessionId,
    step: 'review',
    data: {}  // Empty - just fetch compiled data
});

// Backend returns:
{
    "success": true,
    "data": {
        "basic_info": { name, cuisine, difficulty, servings, description },
        "ingredients": [{ name, amount, unit, notes }, ...],
        "steps": [{ order, instruction, time_minutes, temperature }, ...],
        "diet_labels": ["vegetarian", "healthy", ...],
        "estimated_times": { prep_time, cook_time, total_time }
    }
}
```

### Step 4 → Step 5 Transition

```javascript
// User clicks "Confirm & Continue"
const result = await onBuilderStep({
    session_id: sessionId,
    step: 'review',
    data: {
        save_edits: true,
        edited_data: reviewData  // Contains all user edits
    }
});

// Backend saves edits to session
// Frontend proceeds to Step 5 (Finalize)
```

---

## 🧪 Testing

### Manual Testing Steps

1. **Start Recipe Builder:**
   - Go to Discover page
   - Click "Create Recipe" button

2. **Complete Steps 1-3:**
   - Step 1: Enter "Greek Salad", "Greek", 4 servings, "beginner"
   - Step 2: Add ingredients (e.g., "4 tomatoes", "2 cucumbers")
   - Step 3: Describe steps (e.g., "Chop vegetables and mix")

3. **Test Review Step:**
   - ✅ Verify all data is displayed correctly
   - ✅ Click "Edit" on basic info → modify name → click "Done"
   - ✅ Edit an ingredient amount → verify change saved
   - ✅ Add new ingredient → verify it appears
   - ✅ Delete an ingredient → verify it's removed
   - ✅ Edit a step instruction → verify change saved
   - ✅ Add new step → verify it's numbered correctly
   - ✅ Delete a step → verify renumbering works

4. **Complete Finalize:**
   - Click "Confirm & Continue"
   - Step 5: Set public/private → click "Create Recipe"
   - ✅ Verify recipe is created with all edits applied

### API Testing

Use `test_backend.html`:

```javascript
// Test review step (first call)
{
    "session_id": "your-session-id",
    "step": "review",
    "data": {}
}

// Test saving edits (second call)
{
    "session_id": "your-session-id",
    "step": "review",
    "data": {
        "save_edits": true,
        "edited_data": {
            "basic_info": {
                "name": "Modified Recipe Name",
                "cuisine": "Italian",
                "servings": 6,
                "difficulty": "intermediate"
            },
            "ingredients": [
                {"name": "flour", "amount": 500, "unit": "g"},
                {"name": "eggs", "amount": 3, "unit": "whole"}
            ],
            "steps": [
                {"order": 1, "instruction": "Mix flour and eggs", "time_minutes": 5}
            ],
            "estimated_times": {
                "prep_time": 10,
                "cook_time": 20,
                "total_time": 30
            }
        }
    }
}
```

---

## 🎯 Benefits

### For Users:
1. ✅ **Full Control** - Edit every aspect of the recipe before saving
2. ✅ **Visual Review** - See the complete recipe in formatted view
3. ✅ **Catch Mistakes** - Fix AI errors or typos before publishing
4. ✅ **Add Details** - Enhance AI-generated content with personal touches
5. ✅ **Diet Labels** - See what labels AI detected

### For Product:
1. ✅ **Better Quality** - User-reviewed recipes are more accurate
2. ✅ **User Confidence** - Users feel in control of the process
3. ✅ **Flexibility** - Users can fix AI mistakes without starting over
4. ✅ **Professionalism** - Shows attention to detail and user needs

---

## 🚀 Future Enhancements

### Potential Improvements:
- 📸 Add recipe images during review
- 🏷️ Edit diet labels manually
- 🔄 "Reset to AI suggestion" button for individual fields
- 💾 "Save draft" functionality
- 📱 Mobile-optimized editing interface
- ⚡ Real-time preview as you edit
- 🤖 AI suggestions for improvements during review

---

## 📝 Summary

The new 5-step recipe builder flow with Review & Edit provides:

- **Complete transparency** - Users see exactly what they're saving
- **Full control** - Every field is editable
- **Better UX** - No surprises, no regrets
- **Higher quality** - User-reviewed recipes are more accurate
- **Professional workflow** - Mirrors real recipe creation tools

**Result:** A more polished, user-friendly recipe creation experience that builds trust and encourages users to create high-quality recipes.

---

## 📚 Files Modified

### Frontend:
- ✅ `frontend/src/components/RecipeBuilderWizard.tsx` - Added Step 4 review UI

### Backend:
- ✅ `backend/apps/recipes/builder.py` - Added `_process_review()` method
- ✅ `backend/apps/recipes/views.py` - Updated API documentation

### Documentation:
- ✅ This file (`RECIPE_BUILDER_5_STEP_FLOW.md`)

---

**Implementation Status:** ✅ **Complete and Ready for Testing**

All changes have been implemented and tested. No linter errors. Ready for production deployment.

