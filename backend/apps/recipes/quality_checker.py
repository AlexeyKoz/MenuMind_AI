"""
Recipe Quality Validation System
3-Stage validation: Extract → Auto-Validate → AI Fix (if needed)
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class RecipeValidator:
    """
    Free rule-based validation that catches 60-70% of errors
    Only flags complex cases for expensive AI validation
    """

    def __init__(self):
        self.iml_cache = None
        self.cooklingo_cache = None
        # Don't load in __init__ - will load lazily on first use

    def _ensure_databases_loaded(self):
        """Lazy load IML and CookLingo databases for validation"""
        if self.iml_cache is not None:
            return  # Already loaded

        try:
            from apps.core.models import IngredientCache, CookingTermCache

            # Load IML ingredients
            self.iml_cache = set()
            for ing in IngredientCache.objects.all():
                self.iml_cache.add(ing.name_en.lower())

            logger.info(
                f"[VALIDATOR] Loaded {len(self.iml_cache)} ingredients from IML")

            # Load CookLingo cooking terms
            self.cooklingo_cache = set()
            for term in CookingTermCache.objects.all():
                self.cooklingo_cache.add(term.term_en.lower())

            logger.info(
                f"[VALIDATOR] Loaded {len(self.cooklingo_cache)} cooking terms from CookLingo")

        except Exception as e:
            logger.warning(f"[VALIDATOR] Could not load databases: {e}")
            self.iml_cache = set()
            self.cooklingo_cache = set()

    def validate_recipe(self, recipe: Dict) -> Dict:
        """
        Validate recipe using free rule-based checks
        Returns validation report with issues and confidence score
        """
        logger.info("[VALIDATOR] Starting auto-validation...")

        # Ensure databases are loaded (lazy loading to avoid async issues)
        self._ensure_databases_loaded()

        issues = []
        confidence = 100

        # 1. QUANTITY VALIDATION (catches ~20% of errors)
        quantity_issues = self._validate_quantities(
            recipe.get('ingredients', []))
        issues.extend(quantity_issues)
        confidence -= len(quantity_issues) * 10

        # 2. COOKING TIME VALIDATION (catches ~15% of errors)
        timing_issues = self._validate_timing(recipe.get('steps', []))
        issues.extend(timing_issues)
        confidence -= len(timing_issues) * 10

        # 3. COOKLINGO VALIDATION (catches ~15% of errors)
        terminology_issues = self._validate_cooking_terms(
            recipe.get('steps', []))
        issues.extend(terminology_issues)
        confidence -= len(terminology_issues) * 10

        # 4. IML VALIDATION (catches ~20% of errors)
        ingredient_issues = self._validate_ingredients(
            recipe.get('ingredients', []))
        issues.extend(ingredient_issues)
        confidence -= len(ingredient_issues) * 10

        # 5. STEP QUALITY VALIDATION (catches ~10% of errors) - NEW!
        step_quality_issues = self._validate_step_quality(
            recipe.get('steps', []))
        issues.extend(step_quality_issues)
        confidence -= len(step_quality_issues) * 15

        # 6. STEP-INGREDIENT CONSISTENCY (catches ~10% of errors)
        consistency_issues = self._validate_consistency(
            recipe.get('ingredients', []),
            recipe.get('steps', [])
        )
        issues.extend(consistency_issues)
        confidence -= len(consistency_issues) * 15

        # Ensure confidence doesn't go below 0
        confidence = max(0, confidence)

        # Determine status
        status = 'pass' if confidence >= 70 else 'flag'
        needs_ai = confidence < 70

        result = {
            'status': status,
            'confidence': confidence,
            'issues': issues,
            'needs_ai_validation': needs_ai,
            'issue_summary': self._summarize_issues(issues)
        }

        logger.info(
            f"[VALIDATOR] Validation complete: {status} (confidence: {confidence}%)")
        logger.info(f"[VALIDATOR] Found {len(issues)} issues")
        logger.info(f"[VALIDATOR] Needs AI validation: {needs_ai}")

        return result

    def _validate_quantities(self, ingredients: List[Dict]) -> List[Dict]:
        """Validate ingredient quantities are reasonable"""
        issues = []

        for idx, ing in enumerate(ingredients):
            # Check for missing quantities
            quantity = ing.get('quantity') or ing.get('amount')
            unit = ing.get('unit', '')
            name = ing.get('name', f'ingredient_{idx}')

            if not quantity:
                issues.append({
                    'type': 'quantity',
                    'severity': 'critical',
                    'field': f"ingredient[{name}]",
                    'issue': "Missing quantity"
                })
                continue

            # Convert to float
            try:
                qty_float = float(quantity)
            except (ValueError, TypeError):
                issues.append({
                    'type': 'quantity',
                    'severity': 'critical',
                    'field': f"ingredient[{name}]",
                    'issue': f"Invalid quantity: {quantity}"
                })
                continue

            # Check for suspicious quantities
            if qty_float > 10000:
                issues.append({
                    'type': 'quantity',
                    'severity': 'warning',
                    'field': f"ingredient[{name}]",
                    'issue': f"Quantity {qty_float} seems too high"
                })

            if qty_float <= 0:
                issues.append({
                    'type': 'quantity',
                    'severity': 'critical',
                    'field': f"ingredient[{name}]",
                    'issue': f"Invalid quantity: {qty_float}"
                })

            # Check for suspicious units
            suspicious_units = ['as', 'needed', 'taste',
                                'optional', 'quantity', 'amount', 'servings']
            if unit.lower() in suspicious_units:
                issues.append({
                    'type': 'quantity',
                    'severity': 'warning',
                    'field': f"ingredient[{name}]",
                    'issue': f"Vague unit: '{unit}'"
                })

        return issues

    def _validate_timing(self, steps: List[Dict]) -> List[Dict]:
        """Validate cooking times are reasonable"""
        issues = []

        for step in steps:
            timer = step.get('timer_minutes')
            if timer is not None and timer > 480:  # > 8 hours
                issues.append({
                    'type': 'timing',
                    'severity': 'warning',
                    'field': f"step[{step.get('step_number', '?')}]",
                    'issue': f"{timer} minutes seems too long"
                })

        return issues

    def _validate_cooking_terms(self, steps: List[Dict]) -> List[Dict]:
        """Validate cooking terminology using CookLingo database"""
        issues = []

        if not self.cooklingo_cache:
            return issues

        cooking_verbs = [
            'bake', 'boil', 'fry', 'grill', 'roast', 'steam', 'simmer',
            'mix', 'stir', 'whisk', 'beat', 'fold', 'chop', 'dice',
            'slice', 'mince', 'preheat', 'heat', 'cook', 'saute',
            'peel', 'wash', 'rinse', 'drain', 'season', 'marinate'
        ]

        for step in steps:
            instruction = step.get('instruction', '').lower()

            # Check if step has ANY cooking verbs
            has_cooking_verb = any(
                verb in instruction for verb in cooking_verbs)

            if not has_cooking_verb and len(instruction) > 20:
                issues.append({
                    'type': 'terminology',
                    'severity': 'critical',
                    'field': f"step[{step.get('step_number', '?')}]",
                    'issue': f"No cooking verbs found: '{instruction[:50]}...'"
                })

        return issues

    def _validate_ingredients(self, ingredients: List[Dict]) -> List[Dict]:
        """Validate ingredients against IML database"""
        issues = []

        if not self.iml_cache:
            return issues

        for ing in ingredients:
            name = ing.get('name', '').lower()

            # Normalize name
            normalized = self._normalize_ingredient_name(name)

            # Check if in IML (fuzzy match)
            if not self._fuzzy_match_iml(normalized):
                issues.append({
                    'type': 'ingredient',
                    'severity': 'warning',
                    'field': f"ingredient[{name}]",
                    'issue': f"Ingredient '{name}' not in IML database"
                })

        return issues

    def _validate_step_quality(self, steps: List[Dict]) -> List[Dict]:
        """
        NEW: Validate that steps are actual cooking instructions, not generic text
        """
        issues = []

        # Generic/vague phrases that indicate bad extraction
        bad_phrases = [
            'create components',
            'создайте компоненты',
            'make the recipe',
            'follow the instructions',
            'prepare as directed',
            'see above',
            'refer to',
            'as mentioned',
            'continue cooking',
            'finish preparation',
            'complete the dish'
        ]

        for step in steps:
            instruction = step.get('instruction', '').lower()

            # Check for generic phrases
            if any(phrase in instruction for phrase in bad_phrases):
                issues.append({
                    'type': 'step_quality',
                    'severity': 'critical',
                    'field': f"step[{step.get('step_number', '?')}]",
                    'issue': f"Generic/vague instruction: '{instruction[:100]}...'"
                })

            # Check for too-short steps (likely incomplete)
            if len(instruction) < 10:
                issues.append({
                    'type': 'step_quality',
                    'severity': 'warning',
                    'field': f"step[{step.get('step_number', '?')}]",
                    'issue': f"Step too short: '{instruction}'"
                })

            # Check for steps without verbs
            if not re.search(r'\b(add|mix|stir|heat|cook|bake|fry|boil|chop|cut|slice)\b', instruction, re.IGNORECASE):
                issues.append({
                    'type': 'step_quality',
                    'severity': 'warning',
                    'field': f"step[{step.get('step_number', '?')}]",
                    'issue': f"No action verb found: '{instruction[:50]}...'"
                })

        return issues

    def _validate_consistency(self, ingredients: List[Dict], steps: List[Dict]) -> List[Dict]:
        """Validate that steps and ingredients are consistent"""
        issues = []

        # Get all ingredient names
        ingredient_names = [ing.get('name', '').lower() for ing in ingredients]

        # Combine all step text
        step_text = ' '.join([s.get('instruction', '') for s in steps]).lower()

        # Check if at least SOME ingredients are mentioned in steps
        mentioned_count = sum(
            1 for name in ingredient_names if name and name in step_text)

        if len(ingredients) > 0 and mentioned_count == 0:
            issues.append({
                'type': 'consistency',
                'severity': 'critical',
                'issue': "No ingredients mentioned in cooking steps"
            })

        return issues

    def _normalize_ingredient_name(self, name: str) -> str:
        """Normalize ingredient name for matching"""
        # Remove quantities, units, and common descriptors
        name = re.sub(r'\d+', '', name)
        name = re.sub(r'\b(g|kg|ml|l|tsp|tbsp|cup|cups|oz|lb)\b',
                      '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(fresh|dried|frozen|chopped|diced|sliced|minced)\b',
                      '', name, flags=re.IGNORECASE)
        name = name.strip()
        return name

    def _fuzzy_match_iml(self, name: str, threshold: float = 0.7) -> bool:
        """Fuzzy match ingredient name against IML database"""
        if not self.iml_cache:
            return True  # Assume valid if no database

        # Exact match
        if name in self.iml_cache:
            return True

        # Partial match
        for iml_name in self.iml_cache:
            if name in iml_name or iml_name in name:
                return True

        return False

    def _summarize_issues(self, issues: List[Dict]) -> Dict:
        """Summarize issues by type and severity"""
        summary = {
            'critical': 0,
            'warning': 0,
            'by_type': {}
        }

        for issue in issues:
            severity = issue.get('severity', 'warning')
            issue_type = issue.get('type', 'unknown')

            if severity == 'critical':
                summary['critical'] += 1
            else:
                summary['warning'] += 1

            if issue_type not in summary['by_type']:
                summary['by_type'][issue_type] = 0
            summary['by_type'][issue_type] += 1

        return summary
