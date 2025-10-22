# 🚀 Sprint 4: 3-Phase Translation System - Implementation Plan

**Date**: October 22, 2025  
**Status**: 🔄 IN PROGRESS  

---

## 🎯 Objective

Implement a smart 3-phase translation workflow that optimizes cost and performance:
- **Phase 1**: Immediate translation to user's language
- **Phase 2**: Background translation to popular third language  
- **Phase 3**: On-demand translation for remaining languages

**Key Changes from Original Plan**:
- ✅ Use **Groq as PRIMARY** (higher free quota, faster)
- ✅ Use **Gemini as FALLBACK** (more accurate, but limited quota)
- ✅ Leverage existing IML + CookLingo services for fast ingredient/term translation
- ✅ Use AI only for contextual content (descriptions, full steps)

---

## 📊 Current State (from Sprints 1-3)

**Already Built**:
- ✅ Sprint 1: Database foundation with `RecipeTranslation` model
- ✅ Sprint 2: IML + CookLingo in-memory services (<1ms lookups)
- ✅ Sprint 3: Universal Validator with Groq/Gemini integration
- ✅ Celery configured and ready
- ✅ Redis configured for caching

**What Needs Enhancement**:
- Translation logic currently synchronous
- No phase tracking
- No background translation tasks
- No smart AI provider selection (Groq primary)

---

## 🏗️ Architecture

### **3-Layer Translation Strategy**

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: IML Ingredients (<1ms)                         │
│   - Use in-memory IML service                           │
│   - Direct dictionary lookup                            │
│   - No AI calls needed                                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: CookLingo Terms (<1ms)                         │
│   - Use in-memory CookLingo service                     │
│   - Direct dictionary lookup                            │
│   - No AI calls needed                                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: AI Contextual Content (~2s)                    │
│   - Title, description, full step instructions          │
│   - Groq PRIMARY (llama-3.3-70b)                        │
│   - Gemini FALLBACK (gemini-2.0-flash-lite)            │
│   - Only for text that needs context                    │
└─────────────────────────────────────────────────────────┘
```

### **3-Phase Workflow**

```
Recipe Created (default language: en)
         ↓
┌────────────────────────────────────────────────┐
│ PHASE 1: Immediate (user opens recipe)        │
│   - Translate to user's language              │
│   - Show loading state on frontend            │
│   - Complete in ~2-3 seconds                   │
│   - Store in RecipeTranslation (completed)     │
└────────────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────────┐
│ PHASE 2: Background (Celery task)             │
│   - Queue translation for popular 3rd language │
│   - e.g., if user=ru, translate to he         │
│   - Runs asynchronously                        │
│   - Complete in ~2-3 seconds (background)      │
│   - Store in RecipeTranslation (completed)     │
└────────────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────────┐
│ PHASE 3: On-Demand (user clicks)              │
│   - User explicitly requests another language  │
│   - Frontend shows "Translating..." modal      │
│   - Complete in ~2-3 seconds                   │
│   - Store in RecipeTranslation (completed)     │
└────────────────────────────────────────────────┘
```

---

## 📝 Implementation Tasks

### **Task 1: Enhance RecipeTranslation Model**
Add phase tracking fields:
- `translation_phase` - immediate/background/on_demand
- `ai_provider` - groq/gemini
- `translation_method` - iml_cooklingo/ai_full

### **Task 2: Create SmartTranslationService**
Central service that orchestrates:
- Layer selection (IML → CookLingo → AI)
- AI provider selection (Groq → Gemini)
- Phase execution (immediate/background/on-demand)

### **Task 3: Create Celery Tasks**
- `translate_recipe_immediate.delay(recipe_id, target_lang)`
- `translate_recipe_background.delay(recipe_id, target_lang)`
- `translate_recipe_on_demand.delay(recipe_id, target_lang)`

### **Task 4: Update Recipe Views**
- Modify `retrieve` endpoint to trigger Phase 1
- Add queue for Phase 2
- Handle Phase 3 requests

### **Task 5: Frontend Updates**
- Show translation loading states
- Poll translation status
- Display completion

---

## 🎯 Success Criteria

**Performance**:
- ✅ Phase 1 (immediate): Complete in <3s
- ✅ Phase 2 (background): Queue immediately, complete asynchronously
- ✅ Phase 3 (on-demand): Complete in <3s
- ✅ Ingredient translation: <1ms (IML)
- ✅ Term translation: <1ms (CookLingo)
- ✅ AI translation: <2.5s (Groq primary)

**Cost Optimization**:
- ✅ Use Groq first (higher free quota)
- ✅ Fall back to Gemini only when Groq fails
- ✅ Cache all translations in database
- ✅ Never re-translate same content

**User Experience**:
- ✅ Instant recipe viewing (show original language first)
- ✅ Fast translation (user's language in <3s)
- ✅ Background preparation (third language ready for next user)
- ✅ On-demand flexibility (any language on request)

---

## 📋 Files to Create/Modify

**New Files**:
1. `backend/apps/core/services/smart_translation_service.py` - Main service
2. `backend/apps/recipes/tasks_translation.py` - Celery tasks
3. `backend/test_sprint4_translation.py` - Test suite

**Modified Files**:
1. `backend/apps/recipes/models.py` - Add phase tracking fields
2. `backend/apps/recipes/views.py` - Update translation triggers
3. `backend/apps/core/services/__init__.py` - Export new service

**Migration**:
1. `backend/apps/recipes/migrations/00XX_add_translation_phases.py`

---

## 🚀 Let's Start!

Ready to implement Sprint 4 with Groq as primary and the 3-phase workflow!

**First Step**: Create the SmartTranslationService that leverages Sprint 2's services and implements the 3-layer approach.

