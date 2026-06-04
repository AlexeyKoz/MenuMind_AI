"""
Universal Recipe Validator - 3-Layer Validation System

Layer 1: IML (Ingredient Master List) - Fast ingredient validation
Layer 2: CookLingo - Cooking term validation  
Layer 3: AI (Gemini + Groq fallback) - Contextual coherence validation

Target Performance: <3 seconds for complete validation

Validation Checks:
- Ingredient amounts (suspicious quantities)
- Ingredient existence (unknown ingredients)
- Cooking term accuracy (proper terminology)
- Recipe coherence (logical flow)
- Safety concerns (allergens, dangerous combinations)
"""
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """Validation severity levels"""
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ValidationLayer(str, Enum):
    """Validation layer identifiers"""
    IML = "iml"
    COOKLINGO = "cooklingo"
    AI = "ai"


@dataclass
class ValidationIssue:
    """Single validation issue"""
    layer: ValidationLayer
    level: ValidationLevel
    field: str  # 'ingredients', 'steps', 'metadata'
    message: str
    suggestion: Optional[str] = None
    location: Optional[str] = None  # e.g., "step 3", "ingredient 2"


@dataclass
class ValidationResult:
    """Complete validation result"""
    is_valid: bool
    overall_score: int  # 0-100
    execution_time_ms: float
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    layer_results: Dict[str, Dict] = field(default_factory=dict)

    def get_issues_by_level(self, level: ValidationLevel) -> List[ValidationIssue]:
        """Get all issues of a specific level"""
        return [issue for issue in self.issues if issue.level == level]

    def get_issues_by_layer(self, layer: ValidationLayer) -> List[ValidationIssue]:
        """Get all issues from a specific layer"""
        return [issue for issue in self.issues if issue.layer == layer]

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues"""
        return any(issue.level == ValidationLevel.CRITICAL for issue in self.issues)


class UniversalValidator:
    """
    Universal Recipe Validator

    3-Layer validation system for recipe validation:
    1. IML Layer: Ingredient validation (<100ms)
    2. CookLingo Layer: Cooking term validation (<100ms)
    3. AI Layer: Contextual validation (<2.8s)

    Total target: <3 seconds
    """

    def __init__(self):
        self._iml_service = None
        self._cooklingo_service = None
        self._gemini_client = None
        self._groq_client = None
        self._stats = {
            'total_validations': 0,
            'avg_time_ms': 0,
            'layer_times': {'iml': 0, 'cooklingo': 0, 'ai': 0}
        }

    def _ensure_services_loaded(self):
        """Lazy load services"""
        if not self._iml_service:
            from apps.core.services import get_iml_service
            self._iml_service = get_iml_service()

        if not self._cooklingo_service:
            from apps.core.services import get_cooklingo_service
            self._cooklingo_service = get_cooklingo_service()

    def validate_recipe(
        self,
        recipe_data: Dict,
        skip_ai: bool = False
    ) -> ValidationResult:
        """
        Validate a complete recipe

        Args:
            recipe_data: Recipe in RCIP 2.0 format
            skip_ai: If True, skip AI layer (for faster validation)

        Returns:
            ValidationResult with all issues found

        Performance: <3s with AI, <200ms without AI
        """
        start_time = time.time()
        self._ensure_services_loaded()

        result = ValidationResult(
            is_valid=True,
            overall_score=100,
            execution_time_ms=0,
            issues=[],
            warnings=[],
            info=[]
        )

        try:
            # Layer 1: IML Validation (Fast)
            logger.info("[VALIDATOR] Layer 1: IML ingredient validation...")
            layer1_start = time.time()
            self._validate_ingredients_iml(recipe_data, result)
            layer1_time = (time.time() - layer1_start) * 1000
            result.layer_results['iml'] = {
                'time_ms': layer1_time,
                'issues_found': len([i for i in result.issues if i.layer == ValidationLayer.IML])
            }
            logger.info(f"[VALIDATOR] Layer 1 complete: {layer1_time:.2f}ms")

            # Layer 2: CookLingo Validation (Fast)
            logger.info("[VALIDATOR] Layer 2: CookLingo term validation...")
            layer2_start = time.time()
            self._validate_steps_cooklingo(recipe_data, result)
            layer2_time = (time.time() - layer2_start) * 1000
            result.layer_results['cooklingo'] = {
                'time_ms': layer2_time,
                'issues_found': len([i for i in result.issues if i.layer == ValidationLayer.COOKLINGO])
            }
            logger.info(f"[VALIDATOR] Layer 2 complete: {layer2_time:.2f}ms")

            # Layer 3: AI Validation (Slower but thorough)
            if not skip_ai:
                logger.info("[VALIDATOR] Layer 3: AI coherence validation...")
                layer3_start = time.time()
                self._validate_coherence_ai(recipe_data, result)
                layer3_time = (time.time() - layer3_start) * 1000
                result.layer_results['ai'] = {
                    'time_ms': layer3_time,
                    'issues_found': len([i for i in result.issues if i.layer == ValidationLayer.AI])
                }
                logger.info(
                    f"[VALIDATOR] Layer 3 complete: {layer3_time:.2f}ms")

            # Calculate overall score and validity
            result.overall_score = self._calculate_score(result)
            result.is_valid = result.overall_score >= 70 and not result.has_critical_issues()

            # Record execution time
            result.execution_time_ms = (time.time() - start_time) * 1000

            # Update stats
            self._update_stats(result)

            logger.info(
                f"[VALIDATOR] ✅ Validation complete: {result.execution_time_ms:.2f}ms")
            logger.info(f"[VALIDATOR]    Score: {result.overall_score}/100")
            logger.info(f"[VALIDATOR]    Issues: {len(result.issues)} total")

            return result

        except Exception as e:
            logger.error(f"[VALIDATOR] ❌ Validation failed: {e}")
            result.is_valid = False
            result.overall_score = 0
            result.issues.append(ValidationIssue(
                layer=ValidationLayer.AI,
                level=ValidationLevel.CRITICAL,
                field='system',
                message=f"Validation system error: {str(e)}"
            ))
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result

    def _validate_ingredients_iml(self, recipe_data: Dict, result: ValidationResult):
        """
        Layer 1: Validate ingredients using IML service

        Checks:
        - Ingredient exists in IML
        - Amount is reasonable
        - Unit is valid
        """
        ingredients = recipe_data.get('canonical', {}).get(
            'structure', {}).get('ingredients', [])

        if not ingredients:
            result.issues.append(ValidationIssue(
                layer=ValidationLayer.IML,
                level=ValidationLevel.CRITICAL,
                field='ingredients',
                message='Recipe has no ingredients',
                suggestion='Add at least one ingredient to the recipe'
            ))
            return

        for idx, ingredient in enumerate(ingredients):
            iml_key = ingredient.get('iml_key')
            amount = ingredient.get('amount')
            unit = ingredient.get('unit', 'g')

            # Check if ingredient exists
            if not iml_key:
                result.issues.append(ValidationIssue(
                    layer=ValidationLayer.IML,
                    level=ValidationLevel.CRITICAL,
                    field='ingredients',
                    message=f"Ingredient {idx + 1} missing IML key",
                    location=f"ingredient {idx + 1}"
                ))
                continue

            ingredient_data = self._iml_service.get_ingredient(iml_key)

            if not ingredient_data:
                result.issues.append(ValidationIssue(
                    layer=ValidationLayer.IML,
                    level=ValidationLevel.WARNING,
                    field='ingredients',
                    message=f"Unknown ingredient: {iml_key}",
                    location=f"ingredient {idx + 1}",
                    suggestion=f"Check spelling or add '{iml_key}' to IML database"
                ))
                continue

            # Validate amount if provided
            if amount is not None:
                is_valid, level, message = self._iml_service.validate_amount(
                    iml_key, amount, unit
                )

                if not is_valid or level != 'ok':
                    validation_level = {
                        'ok': ValidationLevel.OK,
                        'info': ValidationLevel.INFO,
                        'warning': ValidationLevel.WARNING,
                        'critical': ValidationLevel.CRITICAL
                    }.get(level, ValidationLevel.WARNING)

                    result.issues.append(ValidationIssue(
                        layer=ValidationLayer.IML,
                        level=validation_level,
                        field='ingredients',
                        message=message,
                        location=f"ingredient {idx + 1}: {iml_key}"
                    ))

    def _validate_steps_cooklingo(self, recipe_data: Dict, result: ValidationResult):
        """
        Layer 2: Validate cooking steps using CookLingo service

        Checks:
        - Cooking terms are recognized
        - Temperature mentions are reasonable
        - Timing is logical
        """
        steps = recipe_data.get('canonical', {}).get(
            'structure', {}).get('steps', [])

        if not steps:
            result.issues.append(ValidationIssue(
                layer=ValidationLayer.COOKLINGO,
                level=ValidationLevel.CRITICAL,
                field='steps',
                message='Recipe has no cooking steps',
                suggestion='Add at least one cooking step'
            ))
            return

        for idx, step in enumerate(steps):
            step_text = step.get('instruction', '')
            cooklingo_actions = step.get('cooklingo_actions', [])

            # Check if step has text
            if not step_text or len(step_text.strip()) < 10:
                result.issues.append(ValidationIssue(
                    layer=ValidationLayer.COOKLINGO,
                    level=ValidationLevel.WARNING,
                    field='steps',
                    message=f'Step {idx + 1} is too short or empty',
                    location=f"step {idx + 1}",
                    suggestion='Add more detailed instructions'
                ))
                continue

            # Detect cooking terms in text
            detected_terms = self._cooklingo_service.detect_terms_in_text(
                step_text, 'en')

            # Check if cooklingo_actions match detected terms
            if cooklingo_actions and detected_terms:
                missing_terms = set(cooklingo_actions) - set(detected_terms)
                if missing_terms:
                    result.issues.append(ValidationIssue(
                        layer=ValidationLayer.COOKLINGO,
                        level=ValidationLevel.INFO,
                        field='steps',
                        message=f'Step {idx + 1}: Listed actions not found in text: {", ".join(missing_terms)}',
                        location=f"step {idx + 1}"
                    ))

            # Info: No cooking terms detected
            if not detected_terms and not cooklingo_actions:
                result.issues.append(ValidationIssue(
                    layer=ValidationLayer.COOKLINGO,
                    level=ValidationLevel.INFO,
                    field='steps',
                    message=f'Step {idx + 1}: No recognized cooking terms',
                    location=f"step {idx + 1}",
                    suggestion='Consider using standard cooking terminology'
                ))

    def _validate_coherence_ai(self, recipe_data: Dict, result: ValidationResult):
        """
        Layer 3: Validate recipe coherence using AI (Gemini + Groq fallback)

        Checks:
        - Recipe makes logical sense
        - Steps are in reasonable order
        - Ingredient quantities match serving size
        - Safety concerns (allergens, dangerous combinations)
        - Cooking times and temperatures are reasonable
        """
        try:
            # Prepare recipe summary for AI
            ingredients = recipe_data.get('canonical', {}).get(
                'structure', {}).get('ingredients', [])
            steps = recipe_data.get('canonical', {}).get(
                'structure', {}).get('steps', [])
            metadata = recipe_data.get('canonical', {}).get('metadata', {})

            ingredient_list = []
            for ing in ingredients:
                iml_key = ing.get('iml_key', 'unknown')
                amount = ing.get('amount', '')
                unit = ing.get('unit', '')
                ingredient_list.append(f"- {iml_key}: {amount}{unit}")

            step_list = []
            for idx, step in enumerate(steps):
                step_text = step.get('instruction', '(no instruction)')
                step_list.append(f"{idx + 1}. {step_text}")

            prompt = f"""Analyze this recipe for coherence and safety issues. Be concise.

Recipe: {metadata.get('title', 'Untitled Recipe')}
Servings: {metadata.get('servings', 'unknown')}

Ingredients:
{chr(10).join(ingredient_list)}

Steps:
{chr(10).join(step_list)}

Check for:
1. Logical step order
2. Missing critical steps (e.g., preheating oven, seasoning)
3. Unrealistic cooking times or temperatures
4. Safety concerns (raw meat handling, allergens)
5. Ingredient-step mismatch (ingredients not used in steps)

Respond in JSON format:
{{
    "issues": [
        {{"severity": "warning|critical", "message": "brief issue description", "suggestion": "optional fix"}}
    ],
    "overall_assessment": "brief 1-sentence summary"
}}

Keep it brief and practical. Only report real issues."""

            # Try Gemini first
            ai_result = self._call_gemini(prompt)

            # Fallback to Groq if Gemini fails
            if not ai_result:
                logger.warning("[VALIDATOR] Gemini failed, trying Groq...")
                ai_result = self._call_groq(prompt)

            if ai_result:
                self._parse_ai_response(ai_result, result)
            else:
                result.issues.append(ValidationIssue(
                    layer=ValidationLayer.AI,
                    level=ValidationLevel.WARNING,
                    field='system',
                    message='AI validation unavailable (both Gemini and Groq failed)',
                    suggestion='Recipe passed basic validation but AI review could not be performed'
                ))

        except Exception as e:
            logger.error(f"[VALIDATOR] AI validation error: {e}")
            result.issues.append(ValidationIssue(
                layer=ValidationLayer.AI,
                level=ValidationLevel.WARNING,
                field='system',
                message=f'AI validation error: {str(e)}'
            ))

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API for validation"""
        try:
            import google.generativeai as genai
            from django.conf import settings

            if not self._gemini_client:
                # Try GEMINI_API_KEY first, then GOOGLE_API_KEY for backwards compatibility
                api_key = getattr(settings, 'GEMINI_API_KEY', None) or getattr(
                    settings, 'GOOGLE_API_KEY', None)
                if not api_key:
                    logger.warning(
                        "[VALIDATOR] No Gemini API key found (GEMINI_API_KEY or GOOGLE_API_KEY)")
                    return None
                genai.configure(api_key=api_key)
                self._gemini_client = genai.GenerativeModel(
                    'gemini-2.5-flash-lite')

            response = self._gemini_client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 500,
                }
            )

            return response.text

        except Exception as e:
            logger.warning(f"[VALIDATOR] Gemini error: {e}")
            return None

    def _call_groq(self, prompt: str) -> Optional[str]:
        """Call Groq API as fallback"""
        try:
            from groq import Groq
            from django.conf import settings

            if not self._groq_client:
                self._groq_client = Groq(api_key=settings.GROQ_API_KEY)

            response = self._groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"[VALIDATOR] Groq error: {e}")
            return None

    def _parse_ai_response(self, ai_response: str, result: ValidationResult):
        """Parse AI response and add issues to result"""
        try:
            import json
            import re

            # Extract JSON from response (might be wrapped in markdown)
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                data = json.loads(json_match.group())

                issues = data.get('issues', [])
                for issue in issues:
                    severity = issue.get('severity', 'warning')
                    level = ValidationLevel.CRITICAL if severity == 'critical' else ValidationLevel.WARNING

                    result.issues.append(ValidationIssue(
                        layer=ValidationLayer.AI,
                        level=level,
                        field='coherence',
                        message=issue.get('message', 'AI detected an issue'),
                        suggestion=issue.get('suggestion')
                    ))

                # Add overall assessment as info
                assessment = data.get('overall_assessment')
                if assessment:
                    result.issues.append(ValidationIssue(
                        layer=ValidationLayer.AI,
                        level=ValidationLevel.INFO,
                        field='summary',
                        message=f"AI Assessment: {assessment}"
                    ))

        except Exception as e:
            logger.error(f"[VALIDATOR] Failed to parse AI response: {e}")
            logger.debug(f"AI Response: {ai_response}")

    def _calculate_score(self, result: ValidationResult) -> int:
        """
        Calculate overall validation score (0-100)

        Scoring:
        - Start with 100
        - Critical issue: -20 points each
        - Warning: -5 points each
        - Info: -1 point each
        - Minimum score: 0
        """
        score = 100

        for issue in result.issues:
            if issue.level == ValidationLevel.CRITICAL:
                score -= 20
            elif issue.level == ValidationLevel.WARNING:
                score -= 5
            elif issue.level == ValidationLevel.INFO:
                score -= 1

        return max(0, score)

    def _update_stats(self, result: ValidationResult):
        """Update validation statistics"""
        self._stats['total_validations'] += 1

        # Update average time
        total_time = self._stats['avg_time_ms'] * \
            (self._stats['total_validations'] - 1)
        total_time += result.execution_time_ms
        self._stats['avg_time_ms'] = total_time / \
            self._stats['total_validations']

        # Update layer times
        for layer, data in result.layer_results.items():
            if layer in self._stats['layer_times']:
                self._stats['layer_times'][layer] = data['time_ms']

    def get_stats(self) -> Dict:
        """Get validator statistics"""
        return self._stats.copy()


# Global singleton instance
universal_validator = UniversalValidator()


def get_universal_validator() -> UniversalValidator:
    """
    Get the global Universal Validator instance

    Usage:
        from apps.core.services.universal_validator import get_universal_validator

        validator = get_universal_validator()
        result = validator.validate_recipe(recipe_data)

        if result.is_valid:
            print(f"Recipe is valid! Score: {result.overall_score}/100")
        else:
            print(f"Issues found: {len(result.issues)}")
    """
    return universal_validator
