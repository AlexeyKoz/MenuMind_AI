"""
RCIP 2.0 Models - Recipe Interchange Protocol Version 2.0

Standardized format for recipe data interchange with full multilingual support.

Features:
- Language-agnostic canonical structure
- Full translation support (en, he, ru)
- IML ingredient keys for consistent identification
- CookLingo action keys for cooking terms
- Validation-ready format
- Export/Import support

Format: JSON (.rcip files)
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class LanguageCode(str, Enum):
    """Supported language codes"""
    EN = "en"
    HE = "he"
    RU = "ru"


class TranslationStatus(str, Enum):
    """Translation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    LOW_CONFIDENCE = "low_confidence"


# ===================================================================
# CANONICAL STRUCTURE (Language-Agnostic)
# ===================================================================

class RCIPIngredient(BaseModel):
    """Ingredient in canonical format"""
    iml_key: str = Field(...,
                         description="IML ingredient key (e.g., 'all-purpose-flour')")
    amount: Optional[float] = Field(None, description="Amount (numeric)")
    unit: Optional[str] = Field(
        None, description="Unit of measurement (g, ml, cup, etc.)")
    processing: Optional[str] = Field(
        None, description="Processing method (diced, chopped, etc.)")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        schema_extra = {
            "example": {
                "iml_key": "all-purpose-flour",
                "amount": 250,
                "unit": "g",
                "processing": "sifted"
            }
        }


class RCIPStep(BaseModel):
    """Cooking step in canonical format"""
    step_id: str = Field(...,
                         description="Unique step identifier (e.g., 'step-1')")
    order: int = Field(..., description="Step order (1-based)")
    instruction: str = Field(...,
                             description="Step instruction text (in source language)")
    cooklingo_actions: List[str] = Field(
        default_factory=list,
        description="CookLingo action keys (e.g., ['dice', 'sauté'])"
    )
    timing: Optional[str] = Field(
        None, description="Time required (e.g., '15min', '1h 30min')")
    temperature: Optional[str] = Field(
        None, description="Temperature (e.g., '180C', '350F')")
    equipment: Optional[List[str]] = Field(
        default_factory=list, description="Required equipment")

    class Config:
        schema_extra = {
            "example": {
                "step_id": "step-1",
                "order": 1,
                "instruction": "Dice the onions and sauté in olive oil until golden brown",
                "cooklingo_actions": ["dice", "sauté"],
                "timing": "5min",
                "temperature": None
            }
        }


class RCIPMetadata(BaseModel):
    """Recipe metadata"""
    title: str = Field(..., description="Recipe title (in source language)")
    description: Optional[str] = Field(None, description="Recipe description")
    source_language: str = Field("en", description="Source language code")
    author_id: Optional[str] = Field(None, description="Author user ID")
    cuisine: Optional[str] = Field(
        None, description="Cuisine type (Italian, Chinese, etc.)")
    category: Optional[str] = Field(
        None, description="Recipe category (dessert, main course, etc.)")
    servings: Optional[int] = Field(None, description="Number of servings")
    prep_time: Optional[int] = Field(
        None, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(
        None, description="Cooking time in minutes")
    total_time: Optional[int] = Field(
        None, description="Total time in minutes")
    difficulty: Optional[str] = Field(
        None, description="Difficulty level (easy, medium, hard)")
    tags: List[str] = Field(default_factory=list, description="Recipe tags")
    image_url: Optional[str] = Field(None, description="Recipe image URL")
    created_at: Optional[str] = Field(
        None, description="Creation timestamp (ISO 8601)")
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp (ISO 8601)")

    class Config:
        schema_extra = {
            "example": {
                "title": "Classic Italian Pasta Carbonara",
                "description": "Traditional Roman pasta with eggs, cheese, and guanciale",
                "source_language": "en",
                "cuisine": "Italian",
                "servings": 4,
                "cook_time": 20,
                "tags": ["pasta", "italian", "quick"]
            }
        }


class RCIPNutrition(BaseModel):
    """Nutritional information (optional)"""
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class RCIPStructure(BaseModel):
    """Recipe structure (canonical, language-agnostic)"""
    ingredients: List[RCIPIngredient] = Field(
        ..., description="List of ingredients")
    steps: List[RCIPStep] = Field(..., description="List of cooking steps")
    nutrition: Optional[RCIPNutrition] = Field(
        None, description="Nutritional information")
    yield_info: Optional[str] = Field(None, description="Yield information")

    @validator('ingredients')
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError("Recipe must have at least one ingredient")
        return v

    @validator('steps')
    def validate_steps(cls, v):
        if not v:
            raise ValueError("Recipe must have at least one step")
        # Validate step order
        orders = [step.order for step in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Step orders must be unique")
        return v


class RCIPCanonical(BaseModel):
    """Canonical recipe data (language-agnostic)"""
    metadata: RCIPMetadata = Field(..., description="Recipe metadata")
    structure: RCIPStructure = Field(..., description="Recipe structure")

    class Config:
        schema_extra = {
            "example": {
                "metadata": {
                    "title": "Simple Pasta",
                    "source_language": "en",
                    "servings": 4
                },
                "structure": {
                    "ingredients": [
                        {"iml_key": "pasta", "amount": 400, "unit": "g"}
                    ],
                    "steps": [
                        {"step_id": "step-1", "order": 1,
                            "instruction": "Boil water"}
                    ]
                }
            }
        }


# ===================================================================
# TRANSLATION DATA (Language-Specific)
# ===================================================================

class RCIPTranslationContent(BaseModel):
    """Translated content for a specific language"""
    title: str = Field(..., description="Translated title")
    description: Optional[str] = Field(
        None, description="Translated description")
    ingredients_text: Dict[str, str] = Field(
        default_factory=dict,
        description="Translated ingredient texts {iml_key: translated_text}"
    )
    steps_text: List[str] = Field(
        default_factory=list,
        description="Translated step instructions"
    )
    tags: List[str] = Field(default_factory=list,
                            description="Translated tags")


class RCIPTranslation(BaseModel):
    """Translation for one language"""
    language: str = Field(..., description="Language code (en, he, ru)")
    status: TranslationStatus = Field(..., description="Translation status")
    confidence: Optional[int] = Field(
        None, description="Translation confidence (0-100)")
    ai_provider: Optional[str] = Field(
        None, description="AI provider used (groq, gemini)")
    translated_at: Optional[str] = Field(
        None, description="Translation timestamp (ISO 8601)")
    needs_review: bool = Field(False, description="Requires human review")
    content: Optional[RCIPTranslationContent] = Field(
        None, description="Translated content")
    error_message: Optional[str] = Field(
        None, description="Error message if failed")

    class Config:
        schema_extra = {
            "example": {
                "language": "he",
                "status": "completed",
                "confidence": 95,
                "ai_provider": "groq",
                "content": {
                    "title": "פסטה פשוטה",
                    "description": "מתכון פשוט לפסטה",
                    "ingredients_text": {"pasta": "400 g פסטה"},
                    "steps_text": ["להרתיח מים"]
                }
            }
        }


# ===================================================================
# VALIDATION DATA (Sprint 3)
# ===================================================================

class RCIPValidationIssue(BaseModel):
    """Validation issue"""
    layer: str = Field(...,
                       description="Validation layer (iml, cooklingo, ai)")
    level: str = Field(...,
                       description="Severity level (ok, info, warning, critical)")
    field: str = Field(..., description="Field with issue")
    message: str = Field(..., description="Issue description")
    suggestion: Optional[str] = Field(None, description="Suggested fix")
    location: Optional[str] = Field(
        None, description="Location (e.g., 'step 3')")


class RCIPValidation(BaseModel):
    """Validation results"""
    is_valid: bool = Field(..., description="Overall validity")
    overall_score: int = Field(..., description="Validation score (0-100)")
    validated_at: Optional[str] = Field(
        None, description="Validation timestamp")
    execution_time_ms: Optional[float] = Field(
        None, description="Validation time in ms")
    issues: List[RCIPValidationIssue] = Field(
        default_factory=list, description="Validation issues")


# ===================================================================
# COMPLETE RCIP 2.0 FORMAT
# ===================================================================

class RCIP20(BaseModel):
    """
    Complete RCIP 2.0 format

    This is the main model for recipe interchange.
    Includes canonical structure, translations, and validation.
    """
    rcip_version: str = Field("2.0", description="RCIP version")
    recipe_id: Optional[str] = Field(
        None, description="Unique recipe ID (UUID)")
    canonical: RCIPCanonical = Field(..., description="Canonical recipe data")
    translations: Dict[str, RCIPTranslation] = Field(
        default_factory=dict,
        description="Translations by language code"
    )
    validation: Optional[RCIPValidation] = Field(
        None, description="Validation results")
    exported_at: Optional[str] = Field(
        None, description="Export timestamp (ISO 8601)")
    export_metadata: Optional[Dict] = Field(
        None, description="Export metadata")

    @validator('rcip_version')
    def validate_version(cls, v):
        if v != "2.0":
            raise ValueError("Only RCIP version 2.0 is supported")
        return v

    def to_json(self) -> str:
        """Export to JSON string"""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'RCIP20':
        """Import from JSON string"""
        return cls.model_validate_json(json_str)

    class Config:
        schema_extra = {
            "example": {
                "rcip_version": "2.0",
                "recipe_id": "550e8400-e29b-41d4-a716-446655440000",
                "canonical": {
                    "metadata": {
                        "title": "Simple Pasta",
                        "source_language": "en",
                        "servings": 4
                    },
                    "structure": {
                        "ingredients": [
                            {"iml_key": "pasta", "amount": 400, "unit": "g"}
                        ],
                        "steps": [
                            {"step_id": "step-1", "order": 1,
                                "instruction": "Boil water"}
                        ]
                    }
                },
                "translations": {
                    "en": {
                        "language": "en",
                        "status": "completed",
                        "content": {
                            "title": "Simple Pasta",
                            "ingredients_text": {"pasta": "400g pasta"},
                            "steps_text": ["Boil water"]
                        }
                    }
                },
                "exported_at": "2025-10-22T10:00:00Z"
            }
        }


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def create_rcip_from_django_recipe(recipe) -> RCIP20:
    """
    Convert Django CanonicalRecipe to RCIP 2.0 format

    Args:
        recipe: CanonicalRecipe instance

    Returns:
        RCIP20 instance
    """
    from apps.recipes.models import RecipeTranslation

    # Build metadata
    metadata = RCIPMetadata(
        title=recipe.name,
        description=recipe.description or "",
        source_language="en",  # Default to English
        servings=4,  # Default
        tags=recipe.tags if hasattr(recipe, 'tags') else [],
        image_url=recipe.image_url if hasattr(recipe, 'image_url') else None,
        created_at=recipe.created_at.isoformat() if hasattr(
            recipe, 'created_at') else None,
        updated_at=recipe.updated_at.isoformat() if hasattr(recipe, 'updated_at') else None
    )

    # Build structure
    ingredients = [
        RCIPIngredient(**ing) for ing in (recipe.base_ingredients or [])
    ]
    steps = [
        RCIPStep(**step) for step in (recipe.base_steps or [])
    ]

    structure = RCIPStructure(
        ingredients=ingredients,
        steps=steps
    )

    canonical = RCIPCanonical(
        metadata=metadata,
        structure=structure
    )

    # Get translations
    translations = {}
    recipe_translations = RecipeTranslation.objects.filter(
        canonical_recipe=recipe)

    for trans in recipe_translations:
        translation_content = None
        if trans.content:
            translation_content = RCIPTranslationContent(**trans.content)

        translations[trans.language] = RCIPTranslation(
            language=trans.language,
            status=TranslationStatus(trans.status),
            confidence=trans.confidence if hasattr(
                trans, 'confidence') else None,
            translated_at=trans.completed_at.isoformat() if hasattr(
                trans, 'completed_at') and trans.completed_at else None,
            content=translation_content
        )

    # Create RCIP
    return RCIP20(
        recipe_id=str(recipe.id),
        canonical=canonical,
        translations=translations,
        exported_at=datetime.utcnow().isoformat() + "Z"
    )


def validate_rcip(rcip: RCIP20) -> bool:
    """
    Validate RCIP 2.0 format

    Args:
        rcip: RCIP20 instance

    Returns:
        True if valid, raises ValidationError otherwise
    """
    # Pydantic handles most validation automatically
    # This function can add additional business logic validation

    # Check that at least source language translation exists
    source_lang = rcip.canonical.metadata.source_language
    if source_lang not in rcip.translations:
        raise ValueError(
            f"Missing translation for source language: {source_lang}")

    return True
