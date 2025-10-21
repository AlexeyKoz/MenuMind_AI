"""
Recipe Generation Progress Tracker
Sends real-time updates via WebSocket to show generation progress
"""

from channels.layers import get_channel_layer
import asyncio
import threading


class RecipeGenerationProgress:
    """Track and broadcast recipe generation progress"""

    # Progress stages with percentages and messages
    STAGES = {
        'searching': {
            'percent': 10,
            'en': 'Searching the internet for recipes...',
            'ru': 'Ищем рецепты в интернете...',
            'he': 'מחפשים מתכונים באינטרנט...'
        },
        'scraping': {
            'percent': 25,
            'en': 'Found recipes! Extracting content...',
            'ru': 'Нашли рецепты! Извлекаем содержимое...',
            'he': 'מצאנו מתכונים! מחלצים תוכן...'
        },
        'converting': {
            'percent': 40,
            'en': 'Converting recipe to standard format...',
            'ru': 'Преобразуем рецепт в стандартный формат...',
            'he': 'ממירים מתכון לפורמט סטנדרטי...'
        },
        'enriching': {
            'percent': 55,
            'en': 'Adding nutritional information...',
            'ru': 'Добавляем информацию о питании...',
            'he': 'מוסיפים מידע תזונתי...'
        },
        'validating': {
            'percent': 70,
            'en': 'Checking recipe quality...',
            'ru': 'Проверяем качество рецепта...',
            'he': 'בודקים איכות מתכון...'
        },
        'translating': {
            'percent': 85,
            'en': 'Translating to your language...',
            'ru': 'Переводим на ваш язык...',
            'he': 'מתרגמים לשפה שלך...'
        },
        'finalizing': {
            'percent': 95,
            'en': 'Almost done! Finalizing recipe...',
            'ru': 'Почти готово! Завершаем рецепт...',
            'he': 'כמעט סיימנו! מסיימים מתכון...'
        },
        'complete': {
            'percent': 100,
            'en': 'Recipe ready! 🎉',
            'ru': 'Рецепт готов! 🎉',
            'he': 'המתכון מוכן! 🎉'
        }
    }

    def __init__(self, user_id: str, language: str = 'en'):
        """
        Initialize progress tracker

        Args:
            user_id: User UUID to send updates to
            language: User's preferred language (en, ru, he)
        """
        self.user_id = user_id
        self.language = language
        self.channel_layer = get_channel_layer()
        self.group_name = f"user_{user_id}"

    def send_progress(self, stage: str, custom_message: str = None):
        """
        Send progress update via WebSocket

        Args:
            stage: Stage key from STAGES dict
            custom_message: Optional custom message to override default
        """
        if stage not in self.STAGES:
            print(f"[PROGRESS] ⚠️ Unknown stage: {stage}")
            return

        stage_data = self.STAGES[stage]
        percent = stage_data['percent']

        # Get message in user's language
        if custom_message:
            message = custom_message
        else:
            message = stage_data.get(self.language, stage_data['en'])

        # Send via WebSocket in a separate thread to avoid event loop conflicts
        def send_in_thread():
            try:
                print(f"[PROGRESS] Sending to group: {self.group_name}")
                print(
                    f"[PROGRESS] Stage: {stage}, Percent: {percent}, Message: {message}")

                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                loop.run_until_complete(
                    self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'recipe_progress',
                            'data': {
                                'stage': stage,
                                'percent': percent,
                                'message': message
                            }
                        }
                    )
                )
                loop.close()
                print(f"[PROGRESS] ✅ Sent: {percent}% - {message}")
            except Exception as e:
                print(f"[PROGRESS] ⚠️ Failed to send update: {e}")
                import traceback
                traceback.print_exc()

        thread = threading.Thread(target=send_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=1.0)  # Wait max 1 second

    def update_searching(self):
        """Stage 1: Searching the internet"""
        self.send_progress('searching')

    def update_scraping(self, found_count: int = None):
        """Stage 2: Scraping recipe content"""
        if found_count:
            custom_msg = {
                'en': f'Found {found_count} recipes! Extracting content...',
                'ru': f'Нашли {found_count} рецептов! Извлекаем содержимое...',
                'he': f'מצאנו {found_count} מתכונים! מחלצים תוכן...'
            }.get(self.language, f'Found {found_count} recipes! Extracting content...')
            self.send_progress('scraping', custom_msg)
        else:
            self.send_progress('scraping')

    def update_converting(self):
        """Stage 3: Converting to RCIP format"""
        self.send_progress('converting')

    def update_enriching(self):
        """Stage 4: Adding nutrition data"""
        self.send_progress('enriching')

    def update_validating(self):
        """Stage 5: Quality validation"""
        self.send_progress('validating')

    def update_translating(self):
        """Stage 6: Translation"""
        self.send_progress('translating')

    def update_finalizing(self):
        """Stage 7: Final steps"""
        self.send_progress('finalizing')

    def update_complete(self):
        """Stage 8: Complete!"""
        self.send_progress('complete')

    def update_error(self, error_message: str = None):
        """Send error message"""
        message = error_message or {
            'en': 'Sorry, something went wrong. Please try again.',
            'ru': 'Извините, что-то пошло не так. Попробуйте еще раз.',
            'he': 'מצטערים, משהו השתבש. אנא נסה שוב.'
        }.get(self.language, 'Sorry, something went wrong.')

        def send_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                loop.run_until_complete(
                    self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'recipe_progress',
                            'data': {
                                'stage': 'error',
                                'percent': 0,
                                'message': message,
                                'error': True
                            }
                        }
                    )
                )
                loop.close()
                print(f"[PROGRESS] ERROR - {message}")
            except Exception as e:
                print(f"[PROGRESS] ⚠️ Failed to send error: {e}")

        thread = threading.Thread(target=send_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=1.0)
