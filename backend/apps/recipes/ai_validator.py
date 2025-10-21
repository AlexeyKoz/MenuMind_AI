"""
AI Re-Validation Service (Stage 3)
Only used for recipes that fail auto-validation
Uses Gemini 2.5 Flash with thinking mode for complex cases
"""

import logging
import json
import google.generativeai as genai
from django.conf import settings
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class AIRecipeValidator:
    """
    AI-powered recipe validation and fixing
    Only used when free validation flags issues
    """

    def __init__(self):
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
            logger.warning("[AI_VALIDATOR] Gemini API key not found")

    def fix_recipe(self, recipe: Dict, validation_report: Dict) -> Optional[Dict]:
        """
        Use AI to fix flagged recipe issues
        Returns fixed recipe or None if unfixable
        """
        if not self.model:
            logger.error(
                "[AI_VALIDATOR] Cannot fix recipe - no AI model available")
            return None

        logger.info(
            "[AI_VALIDATOR] Using Gemini 2.5 Flash to fix recipe issues...")

        # Build prompt with issues
        prompt = self._build_fix_prompt(recipe, validation_report)

        try:
            response = self.model.generate_content(prompt)
            fixed_recipe_text = response.text.strip()

            # Extract JSON from response
            fixed_recipe = self._extract_json(fixed_recipe_text)

            if fixed_recipe:
                logger.info("[AI_VALIDATOR] ✅ Recipe fixed by AI")
                return fixed_recipe
            else:
                logger.error("[AI_VALIDATOR] ❌ AI could not fix recipe")
                return None

        except Exception as e:
            logger.error(f"[AI_VALIDATOR] ❌ AI validation failed: {e}")
            return None

    def _build_fix_prompt(self, recipe: Dict, validation_report: Dict) -> str:
        """Build prompt for AI to fix recipe issues"""
        issues_text = self._format_issues(validation_report['issues'])

        prompt = f"""You are a professional recipe editor. A recipe has failed quality validation.

**ORIGINAL RECIPE:**
Name: {recipe.get('name', 'Unknown')}
Ingredients: {len(recipe.get('ingredients', []))}
Steps: {len(recipe.get('steps', []))}

**INGREDIENTS:**
{json.dumps(recipe.get('ingredients', []), indent=2, ensure_ascii=False)}

**STEPS:**
{json.dumps(recipe.get('steps', []), indent=2, ensure_ascii=False)}

**VALIDATION ISSUES (Confidence: {validation_report['confidence']}%):**
{issues_text}

**YOUR TASK:**
Fix ALL critical and warning issues. Return a corrected recipe in JSON format.

**RULES:**
1. **Quantities**: Ensure all ingredients have valid, specific quantities (no "as needed", "to taste", etc.)
2. **Steps**: Each step must be a SPECIFIC cooking action (not "create components" or generic text)
3. **Cooking Terms**: Use proper cooking verbs (chop, mix, heat, bake, etc.)
4. **Consistency**: Steps must reference ingredients from the list
5. **Completeness**: Include ALL necessary steps for cooking this dish
6. **Language**: Keep output in ENGLISH (will be translated later)

**OUTPUT FORMAT (JSON only, no commentary):**
{{
  "name": "Recipe Name",
  "ingredients": [
    {{
      "name": "ingredient name",
      "quantity": 200,
      "unit": "g",
      "preparation": "chopped" (optional)
    }}
  ],
  "steps": [
    {{
      "step_number": 1,
      "instruction": "Specific cooking action",
      "timer_minutes": 10 (if applicable)
    }}
  ]
}}

Return ONLY the JSON, no explanation."""

        return prompt

    def _format_issues(self, issues: List[Dict]) -> str:
        """Format validation issues for prompt"""
        lines = []
        for issue in issues:
            severity = issue.get('severity', 'warning').upper()
            issue_type = issue.get('type', 'unknown')
            message = issue.get('issue', 'Unknown issue')
            field = issue.get('field', '')

            line = f"[{severity}] {issue_type}"
            if field:
                line += f" ({field})"
            line += f": {message}"
            lines.append(line)

        return '\n'.join(lines)

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from AI response"""
        # Try to find JSON in response
        import re

        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)

        # Find JSON object
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            logger.error("[AI_VALIDATOR] No JSON found in response")
            return None

        try:
            recipe = json.loads(json_match.group(0))

            # Validate the fixed recipe has required fields
            if not recipe.get('ingredients'):
                logger.error("[AI_VALIDATOR] Fixed recipe missing ingredients")
                return None

            if not recipe.get('steps'):
                logger.error("[AI_VALIDATOR] Fixed recipe missing steps")
                return None

            logger.info(
                f"[AI_VALIDATOR] Extracted recipe with {len(recipe.get('ingredients', []))} ingredients and {len(recipe.get('steps', []))} steps")

            return recipe
        except json.JSONDecodeError as e:
            logger.error(f"[AI_VALIDATOR] JSON decode error: {e}")
            logger.error(f"[AI_VALIDATOR] Failed text: {text[:500]}")
            return None
