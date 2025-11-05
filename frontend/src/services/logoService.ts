import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface LogoData {
  id: string;
  logo_type: string;
  language_code: string;
  file_url: string;
  alt_text: string;
  is_active: boolean;
  width: number | null;
  height: number | null;
  dimensions: string;
}

export interface LogosResponse {
  navbar_desktop?: LogoData;
  navbar_mobile?: LogoData;
  login_page?: LogoData;
  favicon?: LogoData;
  app_icon?: LogoData;
}

class LogoService {
  private cache: Map<string, LogosResponse> = new Map();
  private cacheExpiry: Map<string, number> = new Map();
  private readonly CACHE_DURATION = 3600000; // 1 hour in ms

  /**
   * Get all logos for a specific language
   * Falls back to static logos if API fails
   */
  async getLogos(lang: string = 'en'): Promise<LogosResponse> {
    const cacheKey = `logos_${lang}`;
    
    // Check cache
    if (this.cache.has(cacheKey)) {
      const expiry = this.cacheExpiry.get(cacheKey) || 0;
      if (Date.now() < expiry) {
        console.log(`[LogoService] Using cached logos for ${lang}`);
        return this.cache.get(cacheKey)!;
      }
    }

    try {
      console.log(`[LogoService] Fetching logos for language: ${lang}`);
      const response = await axios.get(`${API_URL}/api/branding/logos/for_language/`, {
        params: { lang },
        timeout: 5000 // 5 second timeout
      });

      console.log(`[LogoService] Received logos:`, response.data);

      // Cache the response
      this.cache.set(cacheKey, response.data);
      this.cacheExpiry.set(cacheKey, Date.now() + this.CACHE_DURATION);

      return response.data;
    } catch (error) {
      console.error('[LogoService] Error fetching logos:', error);
      // Return empty object - components will use fallback logos
      return {};
    }
  }

  /**
   * Get a specific logo by type and language
   */
  async getLogo(logoType: string, lang: string = 'en'): Promise<LogoData | null> {
    const logos = await this.getLogos(lang);
    return logos[logoType as keyof LogosResponse] || null;
  }

  /**
   * Get navbar logo (desktop or mobile)
   */
  async getNavbarLogo(isMobile: boolean, lang: string = 'en'): Promise<LogoData | null> {
    const logoType = isMobile ? 'navbar_mobile' : 'navbar_desktop';
    return this.getLogo(logoType, lang);
  }

  /**
   * Get login page logo
   */
  async getLoginLogo(lang: string = 'en'): Promise<LogoData | null> {
    return this.getLogo('login_page', lang);
  }

  /**
   * Get favicon
   */
  async getFavicon(lang: string = 'en'): Promise<LogoData | null> {
    return this.getLogo('favicon', lang);
  }

  /**
   * Update favicon dynamically based on language
   */
  async updateFavicon(lang: string = 'en'): Promise<void> {
    try {
      const favicon = await this.getFavicon(lang);
      
      if (favicon && favicon.file_url) {
        console.log(`[LogoService] Updating favicon to:`, favicon.file_url);
        
        // Remove existing favicon links
        const existingLinks = document.querySelectorAll("link[rel*='icon']");
        existingLinks.forEach(link => link.remove());
        
        // Add new favicon
        const link = document.createElement('link');
        link.type = 'image/x-icon';
        link.rel = 'shortcut icon';
        link.href = favicon.file_url;
        document.getElementsByTagName('head')[0].appendChild(link);
      }
    } catch (error) {
      console.error('[LogoService] Error updating favicon:', error);
    }
  }

  /**
   * Clear cache (useful after admin updates logos)
   */
  clearCache(): void {
    console.log('[LogoService] Clearing cache');
    this.cache.clear();
    this.cacheExpiry.clear();
  }

  /**
   * Preload logos for a language (improves perceived performance)
   */
  async preloadLogos(lang: string): Promise<void> {
    await this.getLogos(lang);
  }
}

export default new LogoService();

