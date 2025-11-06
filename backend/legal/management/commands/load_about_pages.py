"""
Management command to load About Us page content into database.

Usage:
    python manage.py load_about_pages
"""
from django.core.management.base import BaseCommand
from legal.models import AboutPage


class Command(BaseCommand):
    help = 'Load About Us page content in multiple languages'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading About Us pages...'))

        # English About Page
        en_content = """# About BishulMe

Welcome to **BishulMe** - your intelligent cooking companion!

## Our Mission

BishulMe is an AI-powered recipe management and meal planning platform designed to transform your cooking experience. We believe that cooking should be enjoyable, accessible, and personalized to your unique needs.

## What We Do

BishulMe combines cutting-edge artificial intelligence with culinary expertise to provide:

- **Smart Recipe Management**: Organize and discover recipes in multiple languages (English, Russian, Hebrew)
- **AI-Powered Recommendations**: Get personalized recipe suggestions based on your preferences and dietary needs
- **Intelligent Shopping Lists**: Automatically generate shopping lists from your meal plans
- **Inventory Management**: Track ingredients and reduce food waste
- **Multilingual Support**: Access recipes and content in your preferred language with full RTL support for Hebrew

## Our Technology

BishulMe is built on modern, robust technologies:

- **Recipe Interchange Protocol (RCIP)**: Our custom format for standardized recipe exchange
- **Ingredient Master List (IML)**: Comprehensive multilingual ingredient database
- **CookLingo**: Standardized cooking terminology across languages
- **AI Coach**: Intelligent meal planning and nutrition guidance (not a substitute for professional advice)

## Privacy & Compliance

We take your privacy seriously. BishulMe is fully compliant with:

- 🇮🇱 **Israel Privacy Protection Law (Amendment No. 13)**
- 🇪🇺 **GDPR (General Data Protection Regulation)**
- 🇺🇸 **CCPA (California Consumer Privacy Act)**

## Contact Us

Have questions or feedback? We'd love to hear from you!

- **Email**: Bishulme@gmail.com
- **Location**: Petah Tikva, Israel
- **GitHub**: [github.com/AlexeyKoz](https://github.com/AlexeyKoz)

## Open Source

BishulMe is committed to open standards. Our RCIP format is available for implementation by third-party applications, fostering a vibrant ecosystem of recipe-sharing tools.

---

**Thank you for choosing BishulMe. Happy cooking! 👨‍🍳**
"""

        # Russian About Page
        ru_content = """# О BishulMe

Добро пожаловать в **BishulMe** - ваш интеллектуальный помощник по готовке!

## Наша Миссия

BishulMe - это платформа для управления рецептами и планирования питания на базе искусственного интеллекта, созданная для того, чтобы преобразить ваш кулинарный опыт. Мы верим, что приготовление пищи должно быть приятным, доступным и персонализированным под ваши уникальные потребности.

## Что Мы Делаем

BishulMe сочетает передовой искусственный интеллект с кулинарным опытом, чтобы предоставить:

- **Умное Управление Рецептами**: Организуйте и находите рецепты на нескольких языках (английский, русский, иврит)
- **Рекомендации на Основе ИИ**: Получайте персонализированные предложения рецептов на основе ваших предпочтений и диетических потребностей
- **Интеллектуальные Списки Покупок**: Автоматически генерируйте списки покупок из ваших планов питания
- **Управление Запасами**: Отслеживайте ингредиенты и сокращайте пищевые отходы
- **Многоязычная Поддержка**: Доступ к рецептам и контенту на вашем предпочтительном языке с полной поддержкой RTL для иврита

## Наша Технология

BishulMe построен на современных, надежных технологиях:

- **Протокол Обмена Рецептами (RCIP)**: Наш собственный формат для стандартизированного обмена рецептами
- **Мастер-Список Ингредиентов (IML)**: Всеобъемлющая многоязычная база данных ингредиентов
- **CookLingo**: Стандартизированная кулинарная терминология на разных языках
- **AI Тренер**: Интеллектуальное планирование питания и рекомендации по питанию (не является заменой профессиональной консультации)

## Конфиденциальность и Соответствие

Мы серьезно относимся к вашей конфиденциальности. BishulMe полностью соответствует:

- 🇮🇱 **Закону Израиля о Защите Персональных Данных (Поправка № 13)**
- 🇪🇺 **GDPR (Общий Регламент по Защите Данных)**
- 🇺🇸 **CCPA (Калифорнийский Закон о Защите Прав Потребителей)**

## Свяжитесь с Нами

Есть вопросы или отзывы? Мы будем рады услышать вас!

- **Email**: Bishulme@gmail.com
- **Местоположение**: Петах-Тиква, Израиль
- **GitHub**: [github.com/AlexeyKoz](https://github.com/AlexeyKoz)

## Открытый Исходный Код

BishulMe привержен открытым стандартам. Наш формат RCIP доступен для реализации сторонними приложениями, способствуя созданию яркой экосистемы инструментов для обмена рецептами.

---

**Спасибо, что выбрали BishulMe. Приятного приготовления! 👨‍🍳**
"""

        # Hebrew About Page
        he_content = """# אודות בישול שלי

ברוכים הבאים ל**בישול שלי** - מלווה הבישול החכם שלך!

## המשימה שלנו

בישול שלי היא פלטפורמה מבוססת בינה מלאכותית לניהול מתכונים ותכנון ארוחות, שנועדה לשנות את חוויית הבישול שלך. אנחנו מאמינים שבישול צריך להיות מהנה, נגיש ומותאם אישית לצרכים הייחודיים שלך.

## מה אנחנו עושים

בישול שלי משלב בינה מלאכותית מתקדמת עם מומחיות קולינרית כדי לספק:

- **ניהול מתכונים חכם**: ארגון וגילוי מתכונים במספר שפות (אנגלית, רוסית, עברית)
- **המלצות מבוססות AI**: קבל הצעות מתכונים מותאמות אישית על בסיס ההעדפות והצרכים התזונתיים שלך
- **רשימות קניות חכמות**: צור אוטומטית רשימות קניות מתוכניות הארוחות שלך
- **ניהול מלאי**: עקוב אחר מרכיבים והפחת בזבוז מזון
- **תמיכה רב-לשונית**: גישה למתכונים ותוכן בשפה המועדפת עליך עם תמיכה מלאה ב-RTL לעברית

## הטכנולוגיה שלנו

בישול שלי בנוי על טכנולוגיות מודרניות וחזקות:

- **פרוטוקול החלפת מתכונים (RCIP)**: הפורמט המותאם שלנו להחלפת מתכונים סטנדרטית
- **רשימת מרכיבים ראשית (IML)**: מסד נתונים מקיף ורב-לשוני של מרכיבים
- **CookLingo**: טרמינולוגיה קולינרית סטנדרטית בשפות שונות
- **מאמן AI**: תכנון ארוחות חכם והדרכה תזונתית (אינו תחליף לייעוץ מקצועי)

## פרטיות ותאימות

אנחנו לוקחים את הפרטיות שלך ברצינות. בישול שלי תואם לחלוטין ל:

- 🇮🇱 **חוק הגנת הפרטיות הישראלי (תיקון מס' 13)**
- 🇪🇺 **GDPR (התקנה הכללית להגנת מידע)**
- 🇺🇸 **CCPA (חוק הגנת הצרכנים של קליפורניה)**

## צור קשר

יש לך שאלות או משוב? נשמח לשמוע ממך!

- **אימייל**: Bishulme@gmail.com
- **מיקום**: פתח תקווה, ישראל
- **GitHub**: [github.com/AlexeyKoz](https://github.com/AlexeyKoz)

## קוד פתוח

בישול שלי מחויב לסטנדרטים פתוחים. הפורמט RCIP שלנו זמין ליישום על ידי אפליקציות צד שלישי, ומטפח אקוסיסטמה תוססת של כלים לשיתוף מתכונים.

---

**תודה שבחרת בבישול שלי. בישול מהנה! 👨‍🍳**
"""

        pages = [
            {
                'language_code': 'en',
                'title': 'About BishulMe',
                'content': en_content,
                'version': '1.0',
                'meta_description': 'Learn about BishulMe - an AI-powered recipe management and meal planning platform supporting multiple languages and smart cooking features.',
                'meta_keywords': 'about, BishulMe, recipe management, AI cooking, meal planning, multilingual recipes',
            },
            {
                'language_code': 'ru',
                'title': 'О BishulMe',
                'content': ru_content,
                'version': '1.0',
                'meta_description': 'Узнайте о BishulMe - платформе для управления рецептами и планирования питания на базе ИИ с поддержкой нескольких языков и умными функциями готовки.',
                'meta_keywords': 'о нас, BishulMe, управление рецептами, AI кулинария, планирование питания, многоязычные рецепты',
            },
            {
                'language_code': 'he',
                'title': 'אודות בישול שלי',
                'content': he_content,
                'version': '1.0',
                'meta_description': 'למד על בישול שלי - פלטפורמה מבוססת AI לניהול מתכונים ותכנון ארוחות עם תמיכה במספר שפות ותכונות בישול חכמות.',
                'meta_keywords': 'אודות, בישול שלי, ניהול מתכונים, בישול AI, תכנון ארוחות, מתכונים רב-לשוניים',
            },
        ]

        created_count = 0
        updated_count = 0

        for page_data in pages:
            page, created = AboutPage.objects.update_or_create(
                language_code=page_data['language_code'],
                defaults={
                    'title': page_data['title'],
                    'content': page_data['content'],
                    'version': page_data['version'],
                    'meta_description': page_data['meta_description'],
                    'meta_keywords': page_data['meta_keywords'],
                    'is_active': True,
                    'updated_by': 'system'
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Created: {page.title} ({page.language_code})'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'🔄 Updated: {page.title} ({page.language_code})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Done! Created: {created_count}, Updated: {updated_count}'
            )
        )

