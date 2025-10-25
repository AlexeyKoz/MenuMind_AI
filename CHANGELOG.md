# Changelog

All notable changes to MenuMind AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Meal planning calendar with drag-and-drop interface
- Recipe scaling for different serving sizes
- Grocery store integration and price comparison
- Social features: recipe sharing and family meal planning
- Mobile app (iOS/Android)

---

## [0.9.0] - 2025-10-25

### Added
- **Version Control System**: Complete versioning implementation across frontend and backend
- **AI Rate Limiting**: Smart rate limiting for recipe generation (5/minute, 25/day for regular users)
- **Footer Component**: Application-wide footer with version display, copyright, and navigation links
- **Version API Endpoint**: Public `/api/core/version/` endpoint for version information
- **Settings Page Enhancement**: Added detailed version information and system status
- **Rate Limit Exemptions**: Unlimited AI access for testuser1 and testuser2

### Changed
- Updated package.json to version 0.9.0
- Enhanced health check endpoint to include version information
- Improved Settings page UI with version details section
- Footer now displays dynamic version from config

### Fixed
- Rate limiter correctly handles cached recipes (don't count against limits)
- Language switcher state persistence
- Dashboard analytics attribute errors

---

## [0.8.0] - 2025-10-15

### Added
- **AI-Powered Translation**: Full recipe translation in 3 languages (English, Russian, Hebrew)
- **Collaborative Shopping Lists**: Real-time shopping list sharing with WebSocket support
- **Nutrition Tracking Dashboard**: Comprehensive nutrition analytics and insights
- **Google OAuth Authentication**: One-click sign-in with Google
- **Email Verification**: Secure email verification flow for manually registered users
- **Multilingual UI**: Complete interface translation with i18next
- **Email Verification Banner**: User-friendly banner with resend functionality

### Changed
- Improved recipe discovery algorithm with better relevance scoring
- Enhanced mobile responsiveness across all pages
- Updated authentication flow to support both manual and Google sign-in
- Refactored analytics services for better performance

### Fixed
- Translation caching issues causing stale data
- WebSocket reconnection handling for shopping lists
- Email verification link pointing to wrong URL
- Dashboard crash due to incorrect nutrition settings attribute

---

## [0.7.0] - 2025-10-01

### Added
- **Recipe Discovery with AI**: AI-powered recipe suggestions from inventory
- **Shopping List Collaboration**: Multi-user shopping list management
- **Inventory Management**: Track ingredients with expiration dates
- **Two-Tier Caching**: Redis + PostgreSQL caching for recipe generation
- **Recipe Validation**: Automatic recipe validation before storage

### Changed
- Database schema optimization for better query performance
- API response structure improvements
- Enhanced error handling across all endpoints

### Fixed
- Recipe ingredient parsing accuracy
- Inventory item categorization
- Cache invalidation logic

---

## [0.6.0] - 2025-09-15

### Added
- Canonical recipe system with standardized format
- Recipe categorization and tagging
- Search functionality for recipes
- User dietary preferences and restrictions

### Changed
- Improved recipe data model
- Enhanced nutrition calculation accuracy

### Fixed
- Recipe duplication issues
- Ingredient unit conversion bugs

---

## [0.5.0] - 2025-09-01

### Added
- Basic nutrition tracking
- Recipe import from external sources
- User profile management
- Recipe favorites and bookmarks

### Changed
- Updated UI theme and branding
- Improved navigation structure

---

## [0.1.0] - 2025-08-01

### Added
- Initial project setup with Django + React
- Basic recipe CRUD operations
- User authentication (username/password)
- PostgreSQL database integration
- REST API with Django REST Framework
- Basic frontend with React and TypeScript

---

## Version Format

We use **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR** version for incompatible API changes (breaking changes)
- **MINOR** version for new functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

### Version 0.x.x (Pre-Release)
Current pre-release versions. Breaking changes may occur between minor versions. We're iterating fast and improving the platform based on feedback.

### Version 1.0.0+ (Production)
Future production releases. Breaking changes will only occur in major versions, with proper deprecation warnings.

---

## Categories

- **Added**: New features and capabilities
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed in future versions (with migration guide)
- **Removed**: Features that have been removed
- **Fixed**: Bug fixes and corrections
- **Security**: Security vulnerability fixes

---

## Migration Guides

### Upgrading to 0.9.0
No breaking changes. All features are backward compatible with 0.8.0.

### Upgrading to 0.8.0
- Google OAuth requires new environment variables: `GOOGLE_CLIENT_ID`
- Email verification requires SMTP configuration (or console backend for dev)
- New database migrations for `allauth` integration

---

## Release Notes

### What's Next?

**Version 1.0.0** (Target: 2025-11-15)
- Production-ready release
- Performance optimization
- Complete documentation
- Mobile app beta
- Enhanced AI features

**Version 1.1.0** (Target: 2025-12-01)
- Meal planning calendar
- Recipe scaling
- Grocery store integration

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

*Last Updated: 2025-10-25*
*Current Version: 0.9.0*
*Status: Pre-Release (Beta)*

