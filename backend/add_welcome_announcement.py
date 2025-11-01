import os
import django
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

from apps.core.models import AppUpdate
from django.utils import timezone

def create_welcome_announcement():
    """Create welcome announcement for all languages"""
    
    # Tomorrow's date
    tomorrow = timezone.now() + timedelta(days=1)
    tomorrow_date = tomorrow.strftime('%B %d, %Y')
    
    print("\n" + "="*80)
    print("Creating Welcome Announcement for What's New Page")
    print("="*80 + "\n")
    
    announcements = [
        {
            'language': 'en',
            'title': f'🎉 Welcome to MenuMine AI!',
            'description': f'''Welcome! We are officially launching on {tomorrow_date}!

Thank you to all our new participants for joining us on this exciting journey!

⚠️ **Beta Version Notice**
Please note that this is a beta version of MenuMine AI. Some features may not be fully available or may experience occasional issues as we continue to improve the platform. We appreciate your patience and feedback as we work to make MenuMine AI the best it can be!

Your feedback and support help us improve. Thank you for being part of our community! 🙏'''
        },
        {
            'language': 'ru',
            'title': f'🎉 Добро пожаловать в MenuMine AI!',
            'description': f'''Добро пожаловать! Мы официально запускаемся {tomorrow_date}!

Благодарим всех новых участников за то, что присоединились к нам в этом захватывающем путешествии!

⚠️ **Уведомление о бета-версии**
Обратите внимание, что это бета-версия MenuMine AI. Некоторые функции могут быть не полностью доступны или могут иногда работать с перебоями, пока мы продолжаем улучшать платформу. Мы ценим ваше терпение и обратную связь, пока мы работаем над тем, чтобы сделать MenuMine AI лучшим!

Ваши отзывы и поддержка помогают нам совершенствоваться. Спасибо, что вы являетесь частью нашего сообщества! 🙏'''
        },
        {
            'language': 'he',
            'title': f'🎉 ברוכים הבאים ל-MenuMine AI!',
            'description': f'''ברוכים הבאים! אנחנו משיקים רשמית ב-{tomorrow_date}!

תודה לכל המשתתפים החדשים על שהצטרפו אלינו במסע המרגש הזה!

⚠️ **הודעת גרסת בטא**
שימו לב שזו גרסת בטא של MenuMine AI. חלק מהתכונות עשויות שלא להיות זמינות במלואן או עלולות לחוות בעיות מדי פעם בזמן שאנו ממשיכים לשפר את הפלטפורמה. אנו מעריכים את הסבלנות והמשוב שלכם בזמן שאנו עובדים כדי להפוך את MenuMine AI למיטבו!

המשוב והתמיכה שלכם עוזרים לנו להשתפר. תודה שאתם חלק מהקהילה שלנו! 🙏'''
        }
    ]
    
    created_count = 0
    
    for announcement in announcements:
        try:
            # Check if announcement already exists
            existing = AppUpdate.objects.filter(
                language=announcement['language'],
                title=announcement['title']
            ).first()
            
            if existing:
                print(f"[SKIP] {announcement['language'].upper()} - Welcome announcement already exists")
                continue
            
            # Create new announcement
            update = AppUpdate.objects.create(
                title=announcement['title'],
                description=announcement['description'],
                language=announcement['language'],
                status='completed',
                publish_date=tomorrow,
                is_published=True,
                is_featured=True  # Make it featured so it appears at the top
            )
            
            print(f"[SUCCESS] {announcement['language'].upper()} - Created welcome announcement")
            print(f"  Title: {update.title}")
            print(f"  Publish Date: {update.publish_date.strftime('%B %d, %Y')}")
            print(f"  Featured: {update.is_featured}")
            print()
            
            created_count += 1
            
        except Exception as e:
            print(f"[ERROR] {announcement['language'].upper()} - Failed to create announcement: {e}")
            continue
    
    print("="*80)
    print(f"Created {created_count} new announcements")
    print("="*80 + "\n")
    
    # Show all current updates
    print("\n" + "="*80)
    print("All Current Announcements:")
    print("="*80 + "\n")
    
    all_updates = AppUpdate.objects.filter(is_published=True).order_by('language', '-publish_date')
    for update in all_updates:
        print(f"{update} - {update.publish_date.strftime('%Y-%m-%d')}")
    
    print(f"\nTotal: {all_updates.count()} announcements")

if __name__ == '__main__':
    create_welcome_announcement()

