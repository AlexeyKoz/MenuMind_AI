# -*- coding: utf-8 -*-
"""
Comprehensive Admin Interface for User Management

Features:
- Full user CRUD operations
- Email verification management
- Password management
- Advanced filtering and searching
- Bulk actions
- User statistics
- Email address management (allauth)
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import User, UserPreferences

# Try to import allauth models for email verification management
try:
    from allauth.account.models import EmailAddress, EmailConfirmation
    ALLAUTH_AVAILABLE = True
except ImportError:
    ALLAUTH_AVAILABLE = False


class EmailVerifiedFilter(admin.SimpleListFilter):
    """Custom filter for email verification status"""
    title = 'email verification'
    parameter_name = 'email_verified'

    def lookups(self, request, model_admin):
        return (
            ('verified', 'Verified'),
            ('unverified', 'Not Verified'),
            ('no_record', 'No Email Record'),
        )

    def queryset(self, request, queryset):
        if not ALLAUTH_AVAILABLE:
            return queryset

        if self.value() == 'verified':
            verified_users = EmailAddress.objects.filter(
                verified=True
            ).values_list('user_id', flat=True)
            return queryset.filter(id__in=verified_users)

        elif self.value() == 'unverified':
            unverified_users = EmailAddress.objects.filter(
                verified=False
            ).values_list('user_id', flat=True)
            return queryset.filter(id__in=unverified_users)

        elif self.value() == 'no_record':
            users_with_email = EmailAddress.objects.values_list(
                'user_id', flat=True)
            return queryset.exclude(id__in=users_with_email)

        return queryset


class EmailAddressInline(admin.TabularInline):
    """Inline admin for email addresses (allauth)"""
    model = EmailAddress
    extra = 0
    readonly_fields = ('email', 'verified', 'primary')
    can_delete = True

    fields = ('email', 'verified', 'primary')

    def has_add_permission(self, request, obj=None):
        return False


class UserPreferencesInline(admin.StackedInline):
    """Inline admin for user preferences"""
    model = UserPreferences
    extra = 0
    can_delete = False

    fieldsets = (
        ('Language & Units', {
            'fields': ('language', 'unit_system', 'weight_unit', 'volume_unit', 'temperature_unit')
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User Admin with full management capabilities"""

    # ============= Display Configuration =============

    list_display = (
        'username',
        'email',
        'get_full_name_display',
        'email_verified_status',
        'is_active_status',
        'is_staff_status',
        'preferred_language',
        'last_activity',
        'created_at',
        'actions_column',
    )

    list_display_links = ('username', 'email')

    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        'preferred_language',
        'gender',
        'activity_level',
        'created_at',
        'last_activity',
        EmailVerifiedFilter,
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'id',
        'collaboration_key',
    )

    ordering = ('-created_at',)

    date_hierarchy = 'created_at'

    # ============= Form Configuration =============

    fieldsets = (
        ('🔐 Authentication', {
            'fields': ('username', 'email', 'password')
        }),
        ('👤 Personal Information', {
            'fields': ('first_name', 'last_name', 'birth_date', 'gender')
        }),
        ('📊 Physical Information', {
            'fields': ('height_cm', 'weight_kg', 'activity_level'),
            'classes': ('collapse',)
        }),
        ('🎯 Nutrition Goals', {
            'fields': (
                'daily_calories_goal',
                'daily_protein_goal',
                'daily_carbs_goal',
                'daily_fat_goal'
            ),
            'classes': ('collapse',)
        }),
        ('🥗 Dietary Information', {
            'fields': ('dietary_restrictions', 'allergies'),
            'classes': ('collapse',)
        }),
        ('🌍 Preferences', {
            'fields': (
                'preferred_language',
                'weight_unit',
                'volume_unit',
                'time_format',
                'personal_color'
            ),
            'classes': ('collapse',)
        }),
        ('🤝 Collaboration', {
            'fields': (
                'collaboration_key',
                'shopping_role',
            ),
            'classes': ('collapse',)
        }),
        ('👥 Partner Connection', {
            'fields': (
                'partner',
                'couple_code',
                'couple_connected_at'
            ),
            'classes': ('collapse',)
        }),
        ('🔑 Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('📅 Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'last_activity',
                'last_login',
                'date_joined'
            ),
            'classes': ('collapse',)
        }),
        ('🤖 AI Usage', {
            'fields': (
                'ai_requests_today',
                'ai_requests_reset_at'
            ),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        ('🔐 Required Information', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('👤 Optional Information', {
            'classes': ('wide', 'collapse'),
            'fields': ('first_name', 'last_name', 'preferred_language'),
        }),
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'last_login',
        'date_joined',
    )

    # ============= Inlines =============

    inlines = []

    if ALLAUTH_AVAILABLE:
        inlines.append(EmailAddressInline)

    inlines.append(UserPreferencesInline)

    # ============= Custom Display Methods =============

    def get_full_name_display(self, obj):
        """Display full name or username"""
        full_name = obj.get_full_name()
        return full_name if full_name else format_html(
            '<em style="color: #999;">{}</em>',
            'No name set'
        )
    get_full_name_display.short_description = 'Full Name'

    def email_verified_status(self, obj):
        """Show email verification status with icon"""
        if not ALLAUTH_AVAILABLE:
            return format_html('<span style="color: #999;">N/A</span>')

        try:
            email_address = EmailAddress.objects.get(
                user=obj,
                email=obj.email
            )
            if email_address.verified:
                return format_html(
                    '<span style="color: #10b981; font-weight: bold;">✓ Verified</span>'
                )
            else:
                return format_html(
                    '<span style="color: #ef4444; font-weight: bold;">✗ Not Verified</span>'
                )
        except EmailAddress.DoesNotExist:
            return format_html(
                '<span style="color: #f59e0b;">⚠ No Email Record</span>'
            )
    email_verified_status.short_description = 'Email Status'
    email_verified_status.admin_order_field = 'emailaddress__verified'

    def is_active_status(self, obj):
        """Show active status with color"""
        if obj.is_active:
            return format_html(
                '<span style="color: #10b981;">● Active</span>'
            )
        else:
            return format_html(
                '<span style="color: #ef4444;">● Inactive</span>'
            )
    is_active_status.short_description = 'Status'
    is_active_status.admin_order_field = 'is_active'

    def is_staff_status(self, obj):
        """Show staff status with icon"""
        if obj.is_superuser:
            return format_html(
                '<span style="color: #8b5cf6; font-weight: bold;">👑 Superuser</span>'
            )
        elif obj.is_staff:
            return format_html(
                '<span style="color: #3b82f6; font-weight: bold;">🛡 Staff</span>'
            )
        else:
            return format_html(
                '<span style="color: #6b7280;">👤 User</span>'
            )
    is_staff_status.short_description = 'Role'
    
    def preferred_language(self, obj):
        """Show user's preferred language from UserPreferences"""
        try:
            prefs = UserPreferences.objects.filter(user=obj).first()
            if prefs and prefs.language:
                language_map = {
                    'en': '🇬🇧 English',
                    'ru': '🇷🇺 Russian',
                    'he': '🇮🇱 Hebrew'
                }
                return format_html(
                    '<span style="font-weight: bold;">{}</span>',
                    language_map.get(prefs.language, prefs.language)
                )
            else:
                return format_html('<span style="color: #999;">🇬🇧 English (default)</span>')
        except Exception:
            return format_html('<span style="color: #999;">N/A</span>')
    preferred_language.short_description = 'Language'
    is_staff_status.admin_order_field = 'is_staff'

    def actions_column(self, obj):
        """Quick action buttons"""
        buttons = []

        # View user button
        buttons.append(
            f'<a class="button" href="{reverse("admin:users_user_change", args=[obj.pk])}" '
            f'style="padding: 5px 10px; background: #3b82f6; color: white; text-decoration: none; '
            f'border-radius: 4px; font-size: 12px;">✏️ Edit</a>'
        )

        # Email verification button
        if ALLAUTH_AVAILABLE:
            try:
                email_address = EmailAddress.objects.get(
                    user=obj, email=obj.email)
                if not email_address.verified:
                    buttons.append(
                        f'<a class="button" href="javascript:void(0);" '
                        f'onclick="verifyEmail(\'{obj.pk}\')" '
                        f'style="padding: 5px 10px; background: #10b981; color: white; text-decoration: none; '
                        f'border-radius: 4px; font-size: 12px; margin-left: 5px;">✓ Verify</a>'
                    )
            except EmailAddress.DoesNotExist:
                pass

        return format_html(' '.join(buttons))
    actions_column.short_description = 'Actions'

    # ============= Custom Actions =============

    actions = [
        'verify_email_action',
        'unverify_email_action',
        'activate_users',
        'deactivate_users',
        'make_staff',
        'remove_staff',
        'reset_ai_requests',
    ]

    @admin.action(description='✓ Verify email addresses')
    def verify_email_action(self, request, queryset):
        """Verify email addresses for selected users"""
        if not ALLAUTH_AVAILABLE:
            self.message_user(request, 'Allauth not available', level='error')
            return

        count = 0
        for user in queryset:
            try:
                email_address, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email,
                    defaults={'verified': True, 'primary': True}
                )
                if not email_address.verified:
                    email_address.verified = True
                    email_address.save()
                    count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Error verifying {user.email}: {str(e)}',
                    level='error'
                )

        self.message_user(
            request,
            f'Successfully verified {count} email address(es)',
            level='success'
        )

    @admin.action(description='✗ Unverify email addresses')
    def unverify_email_action(self, request, queryset):
        """Unverify email addresses for selected users"""
        if not ALLAUTH_AVAILABLE:
            self.message_user(request, 'Allauth not available', level='error')
            return

        count = 0
        for user in queryset:
            try:
                email_address = EmailAddress.objects.get(
                    user=user,
                    email=user.email
                )
                email_address.verified = False
                email_address.save()
                count += 1
            except EmailAddress.DoesNotExist:
                pass

        self.message_user(
            request,
            f'Successfully unverified {count} email address(es)',
            level='success'
        )

    @admin.action(description='✓ Activate selected users')
    def activate_users(self, request, queryset):
        """Activate selected users"""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Successfully activated {count} user(s)',
            level='success'
        )

    @admin.action(description='✗ Deactivate selected users')
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Successfully deactivated {count} user(s)',
            level='success'
        )

    @admin.action(description='🛡 Make staff')
    def make_staff(self, request, queryset):
        """Grant staff status to selected users"""
        count = queryset.update(is_staff=True)
        self.message_user(
            request,
            f'Successfully granted staff status to {count} user(s)',
            level='success'
        )

    @admin.action(description='👤 Remove staff status')
    def remove_staff(self, request, queryset):
        """Remove staff status from selected users"""
        count = queryset.update(is_staff=False)
        self.message_user(
            request,
            f'Successfully removed staff status from {count} user(s)',
            level='success'
        )

    @admin.action(description='🔄 Reset AI request counters')
    def reset_ai_requests(self, request, queryset):
        """Reset AI request counters for selected users"""
        count = queryset.update(
            ai_requests_today=0,
            ai_requests_reset_at=timezone.now()
        )
        self.message_user(
            request,
            f'Successfully reset AI counters for {count} user(s)',
            level='success'
        )

    # ============= Change List Customization =============

    def changelist_view(self, request, extra_context=None):
        """Add statistics to the changelist"""
        extra_context = extra_context or {}

        # Calculate statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()

        if ALLAUTH_AVAILABLE:
            verified_users = EmailAddress.objects.filter(verified=True).count()
            unverified_users = total_users - verified_users
        else:
            verified_users = 'N/A'
            unverified_users = 'N/A'

        # Recent activity
        week_ago = timezone.now() - timedelta(days=7)
        active_last_week = User.objects.filter(
            last_activity__gte=week_ago
        ).count()

        extra_context['user_stats'] = {
            'total': total_users,
            'active': active_users,
            'inactive': total_users - active_users,
            'staff': staff_users,
            'verified': verified_users,
            'unverified': unverified_users,
            'active_last_week': active_last_week,
        }

        return super().changelist_view(request, extra_context)


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """Admin for user preferences"""

    list_display = (
        'user',
        'language',
        'unit_system',
        'weight_unit',
        'volume_unit',
        'updated_at'
    )

    list_filter = (
        'language',
        'unit_system',
        'weight_unit',
        'volume_unit'
    )

    search_fields = (
        'user__username',
        'user__email'
    )

    readonly_fields = ('created_at', 'updated_at')


# Note: EmailAddress is already registered by django-allauth
# If you need to customize it, unregister first:
# from allauth.account.admin import EmailAddressAdmin as AllauthEmailAddressAdmin
# admin.site.unregister(EmailAddress)
# Then register your custom admin

# Uncomment below to customize EmailAddress admin
# if ALLAUTH_AVAILABLE:
#     from allauth.account.admin import EmailAddressAdmin as AllauthEmailAddressAdmin
#     admin.site.unregister(EmailAddress)
#
#     @admin.register(EmailAddress)
#     class EmailAddressAdmin(admin.ModelAdmin):
#         """Admin for email addresses"""
#
#         list_display = (
#             'email',
#             'user',
#             'verified_status',
#             'primary_status',
#         )
#
#         list_filter = (
#             'verified',
#             'primary'
#         )
#
#         search_fields = (
#             'email',
#             'user__username',
#             'user__email'
#         )
#
#         readonly_fields = ('user', 'email')
#
#         def verified_status(self, obj):
#             if obj.verified:
#                 return format_html(
#                     '<span style="color: #10b981; font-weight: bold;">✓ Verified</span>'
#                 )
#             else:
#                 return format_html(
#                     '<span style="color: #ef4444; font-weight: bold;">✗ Not Verified</span>'
#                 )
#         verified_status.short_description = 'Status'
#
#         def primary_status(self, obj):
#             if obj.primary:
#                 return format_html(
#                     '<span style="color: #3b82f6;">⭐ Primary</span>'
#                 )
#             else:
#                 return format_html(
#                     '<span style="color: #9ca3af;">Secondary</span>'
#                 )
#         primary_status.short_description = 'Type'
