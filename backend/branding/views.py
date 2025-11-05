"""
API Views for Site Branding.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from .models import SiteLogo, SiteSettings
from .serializers import SiteLogoSerializer, SiteSettingsSerializer


class SiteLogoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for retrieving site logos.
    
    GET /api/branding/logos/ - List all active logos
    GET /api/branding/logos/?lang=en - Filter by language
    GET /api/branding/logos/?type=navbar_desktop - Filter by logo type
    GET /api/branding/logos/for_language/?lang=en - Get all logos for a language (with fallback)
    """
    
    queryset = SiteLogo.objects.filter(is_active=True)
    serializer_class = SiteLogoSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Filter logos based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by language
        lang = self.request.query_params.get('lang')
        if lang:
            queryset = queryset.filter(language_code__in=[lang, 'all'])
        
        # Filter by logo type
        logo_type = self.request.query_params.get('type')
        if logo_type:
            queryset = queryset.filter(logo_type=logo_type)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def for_language(self, request):
        """
        Get all logos for a specific language with fallback to 'all' language.
        
        Usage: GET /api/branding/logos/for_language/?lang=en
        
        Returns a dictionary with logo types as keys and logo data as values.
        """
        lang = request.query_params.get('lang', 'en')
        
        # Try cache first
        cache_key = f'site_logos_{lang}'
        cached_logos = cache.get(cache_key)
        if cached_logos:
            return Response(cached_logos)
        
        # Build response dictionary
        logos = {}
        logo_types = ['navbar_desktop', 'navbar_mobile', 'login_page', 'favicon', 'app_icon']
        
        for logo_type in logo_types:
            # Try language-specific logo first
            logo = SiteLogo.objects.filter(
                logo_type=logo_type,
                language_code=lang,
                is_active=True
            ).first()
            
            # Fallback to 'all' language
            if not logo:
                logo = SiteLogo.objects.filter(
                    logo_type=logo_type,
                    language_code='all',
                    is_active=True
                ).first()
            
            if logo:
                serializer = self.get_serializer(logo)
                logos[logo_type] = serializer.data
        
        # Cache for 1 hour
        cache.set(cache_key, logos, 3600)
        
        return Response(logos)
    
    @action(detail=False, methods=['get'])
    def manifest(self, request):
        """
        Get logos formatted for PWA manifest.
        
        Usage: GET /api/branding/logos/manifest/?lang=en
        """
        lang = request.query_params.get('lang', 'en')
        
        # Get app icon
        icon = SiteLogo.objects.filter(
            logo_type='app_icon',
            language_code__in=[lang, 'all'],
            is_active=True
        ).first()
        
        # Get favicon
        favicon = SiteLogo.objects.filter(
            logo_type='favicon',
            language_code__in=[lang, 'all'],
            is_active=True
        ).first()
        
        icons = []
        if icon:
            icons.append({
                'src': request.build_absolute_uri(icon.file_url),
                'sizes': f'{icon.width}x{icon.height}' if icon.width and icon.height else 'any',
                'type': f'image/{icon.image_file.name.split(".")[-1]}'
            })
        
        if favicon:
            icons.append({
                'src': request.build_absolute_uri(favicon.file_url),
                'sizes': f'{favicon.width}x{favicon.height}' if favicon.width and favicon.height else '32x32',
                'type': f'image/{favicon.image_file.name.split(".")[-1]}'
            })
        
        return Response({'icons': icons})


class SiteSettingsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for retrieving site settings.
    
    GET /api/branding/settings/ - Get site settings
    """
    
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer
    permission_classes = [AllowAny]
    
    def list(self, request):
        """Get the singleton settings instance"""
        # Try cache first
        cached_settings = cache.get('site_settings')
        if cached_settings:
            return Response(cached_settings)
        
        settings = SiteSettings.get_settings()
        serializer = self.get_serializer(settings)
        
        # Cache for 1 hour
        cache.set('site_settings', serializer.data, 3600)
        
        return Response(serializer.data)

