/**
 * Frontend tests for Logo Service
 * 
 * Tests:
 * - Logo fetching for all languages
 * - Caching behavior
 * - Fallback logic
 * - Favicon updates
 */

import logoService, { LogoData, LogosResponse } from '../src/services/logoService';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('LogoService', () => {
  beforeEach(() => {
    // Clear cache before each test
    logoService.clearCache();
    jest.clearAllMocks();
  });

  const mockLogoData: LogosResponse = {
    navbar_desktop: {
      id: '1',
      logo_type: 'navbar_desktop',
      language_code: 'en',
      file_url: 'http://localhost:8000/media/navbar_en.svg',
      alt_text: 'BishulSheli',
      is_active: true,
      width: 200,
      height: 50,
      dimensions: '200x50'
    },
    navbar_mobile: {
      id: '2',
      logo_type: 'navbar_mobile',
      language_code: 'en',
      file_url: 'http://localhost:8000/media/navbar_mobile_en.svg',
      alt_text: 'BishulSheli',
      is_active: true,
      width: 40,
      height: 40,
      dimensions: '40x40'
    },
    login_page: {
      id: '3',
      logo_type: 'login_page',
      language_code: 'en',
      file_url: 'http://localhost:8000/media/login_en.svg',
      alt_text: 'BishulSheli - Sign In',
      is_active: true,
      width: 300,
      height: 100,
      dimensions: '300x100'
    }
  };

  describe('getLogos', () => {
    it('should fetch logos for English', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockLogoData });

      const logos = await logoService.getLogos('en');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        'http://localhost:8000/api/branding/logos/for_language/',
        {
          params: { lang: 'en' },
          timeout: 5000
        }
      );
      expect(logos).toEqual(mockLogoData);
    });

    it('should fetch logos for Russian', async () => {
      const russianLogos = { ...mockLogoData };
      russianLogos.navbar_desktop!.language_code = 'ru';
      mockedAxios.get.mockResolvedValue({ data: russianLogos });

      const logos = await logoService.getLogos('ru');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          params: { lang: 'ru' }
        })
      );
      expect(logos.navbar_desktop?.language_code).toBe('ru');
    });

    it('should fetch logos for Hebrew', async () => {
      const hebrewLogos = { ...mockLogoData };
      hebrewLogos.navbar_desktop!.language_code = 'he';
      mockedAxios.get.mockResolvedValue({ data: hebrewLogos });

      const logos = await logoService.getLogos('he');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          params: { lang: 'he' }
        })
      );
      expect(logos.navbar_desktop?.language_code).toBe('he');
    });

    it('should cache logos for 1 hour', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockLogoData });

      // First call
      await logoService.getLogos('en');
      expect(mockedAxios.get).toHaveBeenCalledTimes(1);

      // Second call (should use cache)
      await logoService.getLogos('en');
      expect(mockedAxios.get).toHaveBeenCalledTimes(1); // Still 1, not 2

      // Third call with different language (should make new request)
      await logoService.getLogos('ru');
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });

    it('should return empty object on API error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('API Error'));

      const logos = await logoService.getLogos('en');

      expect(logos).toEqual({});
    });

    it('should handle timeout gracefully', async () => {
      mockedAxios.get.mockRejectedValue({ code: 'ECONNABORTED' });

      const logos = await logoService.getLogos('en');

      expect(logos).toEqual({});
    });
  });

  describe('getLogo', () => {
    it('should get specific logo by type', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockLogoData });

      const logo = await logoService.getLogo('navbar_desktop', 'en');

      expect(logo).toEqual(mockLogoData.navbar_desktop);
    });

    it('should return null for non-existent logo type', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockLogoData });

      const logo = await logoService.getLogo('non_existent', 'en');

      expect(logo).toBeNull();
    });
  });

  describe('getNavbarLogo', () => {
    beforeEach(() => {
      mockedAxios.get.mockResolvedValue({ data: mockLogoData });
    });

    it('should get desktop navbar logo', async () => {
      const logo = await logoService.getNavbarLogo(false, 'en');

      expect(logo?.logo_type).toBe('navbar_desktop');
    });

    it('should get mobile navbar logo', async () => {
      const logo = await logoService.getNavbarLogo(true, 'en');

      expect(logo?.logo_type).toBe('navbar_mobile');
    });
  });

  describe('getLoginLogo', () => {
    it('should get login page logo', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockLogoData });

      const logo = await logoService.getLoginLogo('en');

      expect(logo?.logo_type).toBe('login_page');
    });
  });

  describe('getFavicon', () => {
    it('should get favicon', async () => {
      const dataWithFavicon = {
        ...mockLogoData,
        favicon: {
          id: '4',
          logo_type: 'favicon',
          language_code: 'en',
          file_url: 'http://localhost:8000/media/favicon.svg',
          alt_text: 'BishulSheli Icon',
          is_active: true,
          width: 32,
          height: 32,
          dimensions: '32x32'
        }
      };
      mockedAxios.get.mockResolvedValue({ data: dataWithFavicon });

      const logo = await logoService.getFavicon('en');

      expect(logo?.logo_type).toBe('favicon');
    });
  });

  describe('updateFavicon', () => {
    it('should update favicon in DOM', async () => {
      const faviconData = {
        favicon: {
          id: '4',
          logo_type: 'favicon',
          language_code: 'en',
          file_url: 'http://localhost:8000/media/favicon.svg',
          alt_text: 'BishulSheli Icon',
          is_active: true,
          width: 32,
          height: 32,
          dimensions: '32x32'
        }
      };
      mockedAxios.get.mockResolvedValue({ data: faviconData });

      // Mock document methods
      const mockLink = document.createElement('link');
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink);
      jest.spyOn(document, 'querySelectorAll').mockReturnValue([] as any);
      const mockAppendChild = jest.fn();
      jest.spyOn(document, 'getElementsByTagName').mockReturnValue([
        { appendChild: mockAppendChild }
      ] as any);

      await logoService.updateFavicon('en');

      expect(mockLink.href).toBe('http://localhost:8000/media/favicon.svg');
      expect(mockLink.rel).toBe('shortcut icon');
      expect(mockAppendChild).toHaveBeenCalledWith(mockLink);
    });

    it('should handle error when updating favicon', async () => {
      mockedAxios.get.mockRejectedValue(new Error('API Error'));

      // Should not throw
      await expect(logoService.updateFavicon('en')).resolves.not.toThrow();
    });
  });

  describe('clearCache', () => {
    it('should clear cached logos', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockLogoData });

      // Fetch and cache
      await logoService.getLogos('en');
      expect(mockedAxios.get).toHaveBeenCalledTimes(1);

      // Clear cache
      logoService.clearCache();

      // Fetch again (should make new request)
      await logoService.getLogos('en');
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });
  });

  describe('preloadLogos', () => {
    it('should preload logos for a language', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockLogoData });

      await logoService.preloadLogos('en');

      expect(mockedAxios.get).toHaveBeenCalled();
    });
  });

  describe('Language-specific tests', () => {
    it('should handle all 3 languages independently', async () => {
      const enLogos = { navbar_desktop: { ...mockLogoData.navbar_desktop!, language_code: 'en' } };
      const ruLogos = { navbar_desktop: { ...mockLogoData.navbar_desktop!, language_code: 'ru' } };
      const heLogos = { navbar_desktop: { ...mockLogoData.navbar_desktop!, language_code: 'he' } };

      mockedAxios.get
        .mockResolvedValueOnce({ data: enLogos })
        .mockResolvedValueOnce({ data: ruLogos })
        .mockResolvedValueOnce({ data: heLogos });

      const en = await logoService.getLogos('en');
      const ru = await logoService.getLogos('ru');
      const he = await logoService.getLogos('he');

      expect(en.navbar_desktop?.language_code).toBe('en');
      expect(ru.navbar_desktop?.language_code).toBe('ru');
      expect(he.navbar_desktop?.language_code).toBe('he');
    });
  });
});

