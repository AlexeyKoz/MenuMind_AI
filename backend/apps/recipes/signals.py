"""
Django Signals for Recipe Social Features

Automatically update denormalized statistics on CanonicalRecipe when:
- Likes are added/removed
- Ratings are added/updated/deleted
- Reviews are added/deleted
- Recipe forks are created
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count, Sum
from .models import RecipeLike, RecipeRating, RecipeReview, Recipe


@receiver(post_save, sender=RecipeLike)
def update_likes_on_save(sender, instance, created, **kwargs):
    """Update total_likes when a like is created"""
    if created:
        canonical = instance.canonical_recipe
        # Count all likes
        total_likes = canonical.likes.count()

        # Update canonical
        canonical.total_saves = total_likes  # Likes treated as saves
        canonical.save(update_fields=['total_saves'])

        print(f"[SIGNAL] Updated likes for {canonical.name}: {total_likes}")


@receiver(post_delete, sender=RecipeLike)
def update_likes_on_delete(sender, instance, **kwargs):
    """Update total_likes when a like is deleted"""
    canonical = instance.canonical_recipe

    # Count remaining likes
    total_likes = canonical.likes.count()

    # Update canonical
    canonical.total_saves = total_likes
    canonical.save(update_fields=['total_saves'])

    print(
        f"[SIGNAL] Updated likes after unlike for {canonical.name}: {total_likes}")


@receiver(post_save, sender=RecipeRating)
def update_ratings_on_save(sender, instance, created, **kwargs):
    """Update average_rating and total_ratings when rating is added/updated"""
    canonical = instance.canonical_recipe

    # Calculate new average
    stats = canonical.ratings.aggregate(
        avg=Avg('rating'),
        count=Count('id')
    )

    canonical.average_rating = stats['avg'] or 0
    canonical.total_ratings = stats['count']
    canonical.save(update_fields=['average_rating', 'total_ratings'])

    action = "added" if created else "updated"
    print(
        f"[SIGNAL] Rating {action} for {canonical.name}: avg={canonical.average_rating:.2f}, total={canonical.total_ratings}")


@receiver(post_delete, sender=RecipeRating)
def update_ratings_on_delete(sender, instance, **kwargs):
    """Update average_rating and total_ratings when rating is deleted"""
    canonical = instance.canonical_recipe

    # Recalculate average
    stats = canonical.ratings.aggregate(
        avg=Avg('rating'),
        count=Count('id')
    )

    canonical.average_rating = stats['avg'] or 0
    canonical.total_ratings = stats['count']
    canonical.save(update_fields=['average_rating', 'total_ratings'])

    print(
        f"[SIGNAL] Rating deleted for {canonical.name}: avg={canonical.average_rating:.2f}, total={canonical.total_ratings}")


@receiver(post_save, sender=RecipeReview)
def update_reviews_on_save(sender, instance, created, **kwargs):
    """Update total_reviews when review is added"""
    if created:
        canonical = instance.canonical_recipe

        # Count approved reviews
        total_reviews = canonical.reviews.filter(is_approved=True).count()

        canonical.total_reviews = total_reviews
        canonical.save(update_fields=['total_reviews'])

        print(
            f"[SIGNAL] Review added for {canonical.name}: total={total_reviews}")


@receiver(post_delete, sender=RecipeReview)
def update_reviews_on_delete(sender, instance, **kwargs):
    """Update total_reviews when review is deleted"""
    canonical = instance.canonical_recipe

    # Count remaining approved reviews
    total_reviews = canonical.reviews.filter(is_approved=True).count()

    canonical.total_reviews = total_reviews
    canonical.save(update_fields=['total_reviews'])

    print(
        f"[SIGNAL] Review deleted for {canonical.name}: total={total_reviews}")


@receiver(post_save, sender=Recipe)
def update_forks_on_save(sender, instance, created, **kwargs):
    """Update total_saves when a fork is created"""
    if created and instance.is_fork and instance.canonical_recipe:
        canonical = instance.canonical_recipe

        # Count all forks
        total_forks = canonical.user_forks.count()

        canonical.total_saves = total_forks
        canonical.save(update_fields=['total_saves'])

        print(
            f"[SIGNAL] Fork created for {canonical.name}: total_forks={total_forks}")


@receiver(post_delete, sender=Recipe)
def update_forks_on_delete(sender, instance, **kwargs):
    """Update total_saves when a fork is deleted"""
    if instance.is_fork and instance.canonical_recipe:
        canonical = instance.canonical_recipe

        # Count remaining forks
        total_forks = canonical.user_forks.count()

        canonical.total_saves = total_forks
        canonical.save(update_fields=['total_saves'])

        print(
            f"[SIGNAL] Fork deleted for {canonical.name}: total_forks={total_forks}")

