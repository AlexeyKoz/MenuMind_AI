from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    Recipe, UserRecipe, CanonicalRecipe,
    RecipeLike, RecipeRating, RecipeReview, RecipeReviewHelpful,
    BulkRecipeGenerationJob
)
from .tasks import process_bulk_recipe_generation


@admin.register(CanonicalRecipe)
class CanonicalRecipeAdmin(admin.ModelAdmin):
    """Admin interface for CanonicalRecipe model"""

    list_display = ['name', 'source_type', 'cuisine', 'difficulty',
                    'total_saves', 'average_rating', 'total_reviews',
                    'is_published', 'is_featured', 'created_at']
    list_filter = ['source_type', 'difficulty', 'cuisine',
                   'is_published', 'is_featured', 'diet_labels']
    search_fields = ['name', 'description']
    readonly_fields = ['recipe_hash', 'total_saves', 'total_cooked', 'total_views',
                       'average_rating', 'total_ratings', 'total_reviews',
                       'created_at', 'updated_at']
    list_editable = ['is_published', 'is_featured']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'source_type', 'ai_source_url', 'original_creator')
        }),
        ('Recipe Content', {
            'fields': ('base_ingredients', 'base_steps')
        }),
        ('Metadata', {
            'fields': ('prep_time_minutes', 'cook_time_minutes', 'total_time_minutes',
                       'servings', 'difficulty', 'cuisine', 'diet_labels')
        }),
        ('Deduplication', {
            'fields': ('recipe_hash',)
        }),
        ('Statistics', {
            'fields': ('total_saves', 'total_cooked', 'total_views',
                       'average_rating', 'total_ratings', 'total_reviews')
        }),
        ('Publication', {
            'fields': ('is_published', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['make_featured', 'remove_featured', 'update_statistics']

    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(
            request, f"{queryset.count()} recipes marked as featured")
    make_featured.short_description = "Mark selected recipes as featured"

    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(
            request, f"{queryset.count()} recipes removed from featured")
    remove_featured.short_description = "Remove featured status"

    def update_statistics(self, request, queryset):
        for recipe in queryset:
            recipe.update_statistics()
        self.message_user(
            request, f"Updated statistics for {queryset.count()} recipes")
    update_statistics.short_description = "Recalculate statistics"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin interface for Recipe model"""

    list_display = ['name', 'created_by', 'is_fork', 'canonical_recipe', 'difficulty',
                    'cuisine', 'version', 'is_latest_version', 'times_cooked', 'created_at']
    list_filter = ['is_fork', 'difficulty',
                   'cuisine', 'is_latest_version', 'diet_labels']
    search_fields = ['name', 'description', 'author']
    readonly_fields = ['recipe_hash', 'version', 'created_at',
                       'updated_at', 'times_added_to_lists', 'times_cooked']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'author', 'source_url', 'created_by')
        }),
        ('Fork System (NEW)', {
            'fields': ('canonical_recipe', 'is_fork', 'user_modifications')
        }),
        ('Recipe Content', {
            'fields': ('ingredients', 'steps')
        }),
        ('Metadata', {
            'fields': ('prep_time_minutes', 'cook_time_minutes', 'total_time_minutes',
                       'servings', 'difficulty', 'cuisine', 'diet_labels')
        }),
        ('Versioning & Deduplication', {
            'fields': ('recipe_hash', 'version', 'parent_recipe', 'is_latest_version')
        }),
        ('Statistics', {
            'fields': ('times_added_to_lists', 'times_cooked')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UserRecipe)
class UserRecipeAdmin(admin.ModelAdmin):
    """Admin interface for UserRecipe model"""

    list_display = ['user', 'recipe', 'rating',
                    'times_cooked', 'last_cooked', 'saved_at']
    list_filter = ['rating', 'saved_at']
    search_fields = ['user__username', 'recipe__name']
    readonly_fields = ['saved_at']

    fieldsets = (
        ('User & Recipe', {
            'fields': ('user', 'recipe')
        }),
        ('User Data', {
            'fields': ('notes', 'rating', 'times_cooked', 'last_cooked')
        }),
        ('Timestamps', {
            'fields': ('saved_at',)
        }),
    )


# ============================================================================
# SOCIAL FEATURES ADMIN
# ============================================================================

@admin.register(RecipeLike)
class RecipeLikeAdmin(admin.ModelAdmin):
    """Admin interface for RecipeLike model"""

    list_display = ['user', 'canonical_recipe', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'canonical_recipe__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(RecipeRating)
class RecipeRatingAdmin(admin.ModelAdmin):
    """Admin interface for RecipeRating model"""

    list_display = ['user', 'canonical_recipe',
                    'rating', 'created_at', 'updated_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'canonical_recipe__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(RecipeReview)
class RecipeReviewAdmin(admin.ModelAdmin):
    """Admin interface for RecipeReview model"""

    list_display = ['user', 'canonical_recipe', 'title', 'rating',
                    'helpful_count', 'is_approved', 'is_reported', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_reported', 'created_at']
    search_fields = ['user__username',
                     'canonical_recipe__name', 'title', 'content']
    readonly_fields = ['helpful_count', 'created_at', 'updated_at']
    list_editable = ['is_approved']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'canonical_recipe', 'title', 'content', 'rating')
        }),
        ('Engagement', {
            'fields': ('helpful_count',)
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_reported')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['approve_reviews', 'flag_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} reviews approved")
    approve_reviews.short_description = "Approve selected reviews"

    def flag_reviews(self, request, queryset):
        queryset.update(is_reported=True)
        self.message_user(request, f"{queryset.count()} reviews flagged")
    flag_reviews.short_description = "Flag selected reviews"


@admin.register(RecipeReviewHelpful)
class RecipeReviewHelpfulAdmin(admin.ModelAdmin):
    """Admin interface for RecipeReviewHelpful model"""

    list_display = ['user', 'review', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'review__canonical_recipe__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


# ============================================================================
# BULK RECIPE GENERATION ADMIN (Developer Tool)
# ============================================================================

@admin.register(BulkRecipeGenerationJob)
class BulkRecipeGenerationJobAdmin(admin.ModelAdmin):
    """Admin interface for Bulk Recipe Generation Jobs"""

    list_display = ['id', 'created_by', 'status_badge', 'progress_bar', 
                    'total_recipes', 'completed_recipes', 'failed_recipes', 
                    'created_at', 'action_buttons']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'created_by__username', 'recipe_list']
    readonly_fields = ['id', 'status', 'total_recipes', 'completed_recipes', 
                       'failed_recipes', 'results', 'celery_task_id', 
                       'created_at', 'started_at', 'completed_at', 'results_display']
    
    fieldsets = (
        ('Job Information', {
            'fields': ('id', 'created_by', 'status', 'celery_task_id')
        }),
        ('Recipe List', {
            'fields': ('recipe_list',),
            'description': 'Enter recipe names to generate, one per line. '
                          'The system will automatically search and scrape each recipe from the internet.'
        }),
        ('Progress', {
            'fields': ('total_recipes', 'completed_recipes', 'failed_recipes')
        }),
        ('Results', {
            'fields': ('results_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-bulk-job/', 
                 self.admin_site.admin_view(self.create_bulk_job_view),
                 name='recipes_bulkrecipegenerationjob_create'),
            path('<path:object_id>/start/', 
                 self.admin_site.admin_view(self.start_job_view),
                 name='recipes_bulkrecipegenerationjob_start'),
        ]
        return custom_urls + urls

    def create_bulk_job_view(self, request):
        """Custom view for creating bulk recipe generation jobs"""
        if request.method == 'POST':
            recipe_list = request.POST.get('recipe_list', '').strip()
            
            if not recipe_list:
                messages.error(request, 'Please provide a recipe list')
                return redirect('..')
            
            # Create job
            job = BulkRecipeGenerationJob.objects.create(
                created_by=request.user,
                recipe_list=recipe_list,
                status='pending'
            )
            
            # Start processing immediately
            process_bulk_recipe_generation.delay(str(job.id))
            
            messages.success(
                request, 
                f'Bulk recipe generation job created! Processing {len(job.get_recipe_names())} recipes. '
                f'Job ID: {job.id}'
            )
            return redirect(f'../{job.id}/change/')
        
        # GET request - show form
        context = {
            'title': 'Create Bulk Recipe Generation Job',
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'has_permission': True,
        }
        return render(request, 'admin/recipes/bulk_recipe_generation_form.html', context)

    def start_job_view(self, request, object_id):
        """Start a pending job"""
        try:
            job = BulkRecipeGenerationJob.objects.get(id=object_id)
            
            if job.status != 'pending':
                messages.warning(request, f'Job is already {job.status}')
            else:
                # Start processing
                process_bulk_recipe_generation.delay(str(job.id))
                messages.success(request, 'Job started successfully!')
            
            return redirect(f'../{object_id}/change/')
        except BulkRecipeGenerationJob.DoesNotExist:
            messages.error(request, 'Job not found')
            return redirect('../')

    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'pending': '#FFA500',  # Orange
            'in_progress': '#007BFF',  # Blue
            'completed': '#28A745',  # Green
            'failed': '#DC3545',  # Red
            'partial': '#FFC107',  # Yellow
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def progress_bar(self, obj):
        """Display progress bar"""
        percentage = obj.get_progress_percentage()
        color = '#28A745' if percentage == 100 else '#007BFF'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 4px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; '
            'line-height: 20px; font-size: 12px; font-weight: bold;">{}</div>'
            '</div>',
            percentage, color, f'{percentage}%'
        )
    progress_bar.short_description = 'Progress'

    def action_buttons(self, obj):
        """Display action buttons"""
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}/start/">Start Job</a>',
                obj.id
            )
        elif obj.status == 'in_progress':
            return format_html(
                '<span style="color: #007BFF;">⏳ Processing...</span>'
            )
        elif obj.status == 'completed':
            return format_html(
                '<span style="color: #28A745;">✅ Complete</span>'
            )
        elif obj.status == 'failed':
            return format_html(
                '<span style="color: #DC3545;">❌ Failed</span>'
            )
        elif obj.status == 'partial':
            return format_html(
                '<span style="color: #FFC107;">⚠️ Partial</span>'
            )
        return '-'
    action_buttons.short_description = 'Actions'

    def results_display(self, obj):
        """Display formatted results"""
        if not obj.results:
            return 'No results yet'
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background-color: #f8f9fa;"><th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Recipe Name</th><th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Status</th><th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Message</th></tr>'
        
        for recipe_name, result in obj.results.items():
            status = result.get('status', 'unknown')
            status_color = '#28A745' if status == 'success' else '#DC3545'
            message = result.get('message', '')
            
            html += f'<tr><td style="padding: 8px; border: 1px solid #dee2e6;">{recipe_name}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #dee2e6;"><span style="color: {status_color}; font-weight: bold;">{status.upper()}</span></td>'
            html += f'<td style="padding: 8px; border: 1px solid #dee2e6;">{message}</td></tr>'
        
        html += '</table>'
        return format_html(html)
    results_display.short_description = 'Detailed Results'

    def has_add_permission(self, request):
        """Allow adding through custom view only"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Add custom button to changelist view"""
        extra_context = extra_context or {}
        extra_context['show_create_button'] = True
        return super().changelist_view(request, extra_context)

