# Project Analysis Prompt for External AI Agent

## Context

You are analyzing the **MenuMindAI** platform - a multi-tenant food intelligence platform with Django backend and React/TypeScript frontend. Your task is to provide a comprehensive codebase analysis that will be used to design and implement a complete testing strategy.

---

## Required Analysis Scope

### 1. BACKEND ANALYSIS (Django + DRF)

#### A. Application Structure

For each Django app (`users`, `recipes`, `shopping`, `nutrition`, `core`, `ai_agents`, `legal`), provide:

1. **Models Analysis:**
   - List all models with their fields, relationships (ForeignKey, ManyToMany, OneToOne)
   - Custom managers and querysets
   - Model methods and properties
   - Validators and constraints
   - Indexes and database optimizations

2. **API Endpoints (DRF):**
   - All ViewSets and APIViews
   - URL patterns and route configurations
   - Request/response serializers
   - Permissions classes used
   - Authentication requirements
   - Query parameters and filters
   - Pagination settings

3. **Business Logic & Services:**
   - Service classes and functions
   - Complex business logic not in views
   - Utility functions
   - Data transformation logic
   - Integration points between apps

4. **Permissions & Authorization:**
   - Custom permission classes
   - Row-level permissions
   - Object ownership checks
   - Role-based access control
   - Collaboration permissions (for shopping lists)

5. **Validators & Forms:**
   - Custom field validators
   - Serializer validators
   - Form validation logic
   - Data sanitization

#### B. Authentication & Security

1. **Auth System:**
   - JWT token implementation (SimpleJWT)
   - Email verification flow
   - Google OAuth implementation
   - Password reset flow
   - Token refresh mechanism
   - Session management

2. **Security Features:**
   - CORS configuration
   - Rate limiting
   - Input sanitization
   - SQL injection prevention
   - XSS protection measures

#### C. Async & Background Tasks

1. **Celery Tasks:**
   - All defined tasks with their signatures
   - Task schedules (Celery Beat)
   - Task dependencies
   - Error handling and retries
   - Task result backends

2. **WebSocket Consumers:**
   - Django Channels consumers
   - WebSocket routing
   - Group management
   - Real-time event handling
   - Authentication in WebSockets

#### D. AI & External Integrations

1. **AI Services:**
   - Groq integration (models used, endpoints)
   - Gemini integration (models used, endpoints)
   - Anthropic integration
   - Prompt engineering patterns
   - Fallback mechanisms
   - Rate limiting and quota management

2. **Translation System:**
   - IML (Ingredient Multilingual Library) service
   - CookLingo glossary service
   - Translation cache mechanism
   - Translation pipeline workflow
   - Language support (EN/RU/HE)

3. **External APIs:**
   - DuckDuckGo search integration
   - Web scraping utilities
   - Recipe discovery mechanisms
   - RCIP 2.0 import/export

#### E. Data Management

1. **Database:**
   - PostgreSQL schema
   - Migrations history
   - Custom migrations
   - Database indexes
   - Query optimization patterns

2. **Caching:**
   - Redis cache keys structure
   - Cache invalidation logic
   - Discovery cache system
   - Translation cache
   - Session storage

3. **File Storage:**
   - Media file handling
   - Static files management
   - Image processing
   - File upload validators

#### F. Signals & Hooks

- All Django signals registered
- Signal handlers and their logic
- Post-save, pre-save operations
- Model lifecycle hooks

---

### 2. FRONTEND ANALYSIS (React + TypeScript)

#### A. Component Architecture

1. **Component Inventory:**
   - All React components (pages, layouts, shared components)
   - Component hierarchy and relationships
   - Props interfaces (TypeScript)
   - Component state management
   - Side effects (useEffect usage)

2. **Context Providers:**
   - AuthContext implementation
   - CollaborationProvider
   - Other context providers
   - Context consumption patterns

#### B. State Management

1. **Global State:**
   - Context-based state
   - LocalStorage usage
   - Session management
   - State persistence strategies

2. **Forms & Validation:**
   - Form components
   - Validation logic (client-side)
   - Form submission handling
   - Error state management

#### C. API Integration

1. **API Client:**
   - Axios/fetch configuration
   - Base URL configuration
   - Request interceptors
   - Response interceptors
   - Error handling
   - Token attachment logic

2. **API Calls:**
   - All API endpoints called from frontend
   - Request/response types
   - Error handling patterns
   - Loading states
   - Retry logic

#### D. Routing & Navigation

1. **Routes:**
   - All route definitions
   - Protected routes
   - Route guards
   - Navigation patterns
   - Redirect logic

2. **URL Parameters:**
   - Dynamic routes
   - Query parameters usage
   - Navigation state

#### E. Real-time Features

1. **WebSocket Client:**
   - WebSocket connection management
   - Message handling
   - Reconnection logic
   - Event subscriptions
   - State synchronization

#### F. Internationalization

1. **i18next Configuration:**
   - Translation keys structure
   - Language switching mechanism
   - RTL support (Hebrew)
   - Translation loading
   - Fallback strategies

#### G. UI/UX Features

1. **Components:**
   - UI component library usage
   - Custom components
   - Accessibility features
   - Responsive design patterns

2. **User Feedback:**
   - Toast notifications
   - Loading indicators
   - Error messages
   - Success confirmations

---

### 3. INTEGRATION POINTS

Map out all critical integration points between:
- Frontend ↔ Backend APIs
- Backend ↔ AI Services
- Backend ↔ External APIs
- Backend ↔ Database
- Backend ↔ Redis/Cache
- Backend ↔ Celery Tasks
- Frontend ↔ WebSocket Server

---

### 4. CONFIGURATION & ENVIRONMENT

1. **Environment Variables:**
   - All required environment variables
   - Configuration for different environments (dev/staging/prod)
   - Secrets management

2. **Settings:**
   - Django settings modules
   - Feature flags
   - Third-party library configurations

---

### 5. ERROR HANDLING & LOGGING

1. **Backend:**
   - Exception handling patterns
   - Custom exception classes
   - Error response formats
   - Logging configuration
   - Error tracking

2. **Frontend:**
   - Error boundaries
   - Global error handlers
   - User-facing error messages
   - Error logging/reporting

---

### 6. DEPENDENCIES & VERSIONS

List all critical dependencies with versions:
- Backend: Django, DRF, Celery, Channels, etc.
- Frontend: React, TypeScript, libraries
- AI: SDK versions for Groq, Gemini, Anthropic
- Infrastructure: Redis, PostgreSQL versions

---

## Output Format

Please provide the analysis in the following structure:

```markdown
# MenuMindAI Codebase Analysis for Testing

## 1. Backend Django Apps

### 1.1 Users App
#### Models
[Detailed model analysis...]

#### API Endpoints
[Complete endpoint documentation...]

#### Services & Business Logic
[Service layer analysis...]

[Continue for all apps...]

## 2. Frontend React App

### 2.1 Components
[Component inventory...]

### 2.2 API Integration
[API client analysis...]

[Continue for all sections...]

## 3. Integration Map
[Visual or textual map of integrations...]

## 4. Critical Paths
[Identify critical user flows and data paths...]

## 5. Risk Areas
[Identify complex/risky areas that need thorough testing...]

## 6. Test Data Requirements
[Types of test data needed...]
```

---

## Special Attention Areas

Please pay extra attention to:

1. **Authentication flows** - JWT, email verification, Google OAuth
2. **Real-time shopping lists** - WebSocket implementation
3. **AI translation pipeline** - Multi-tier translation with caching
4. **Multilingual support** - EN/RU/HE with RTL
5. **Celery background tasks** - Translation jobs, discovery cache refresh
6. **Permission system** - Especially shopping list collaboration
7. **Legal compliance** - GDPR/CCPA data export/deletion
8. **Recipe CRUD** - Including RCIP import/export
9. **Nutrition tracking** - AI meal logging, analytics
10. **Discovery system** - Cache management, search

---

## Goal

The analysis should provide enough detail to design:
- **Unit tests** for all backend models, serializers, services
- **Integration tests** for API endpoints, workflows
- **E2E tests** for critical user journeys
- **Performance tests** for caching, real-time features
- **Security tests** for authentication, permissions
- **Frontend unit tests** for components, hooks, utilities
- **Frontend integration tests** for user flows
- **Contract tests** for API integration

---

## Usage Instructions

This prompt is designed to be used with:
- **Claude Projects** - Load the entire codebase as context
- **ChatGPT with Code Interpreter** - Upload codebase or provide file access
- **Testing Specialist** - Human analyst reviewing the codebase
- **AI-powered documentation tools** - Automated analysis systems

**Recommended Approach:**
1. Load the entire MenuMindAI codebase into your AI workspace
2. Provide this prompt
3. Allow 2-4 hours of analysis time
4. Request specific sections if the full analysis is too large
5. Generate test plans based on the analysis output

---

**Note:** This analysis will be used by a testing specialist to create a comprehensive test suite covering both backend and frontend. Please be thorough and include code examples where relevant.

---

## Related Documents

- `README.md` - Project overview and setup instructions
- `docs/external_agent_overview.md` - External agent integration details
- `docs/rate_limiting_quota_design.md` - Rate limiting architecture
- `docs/emailjs_integration_brief.md` - Email service integration
- `docs/google_oauth_email_verification.md` - OAuth flow documentation

---

**Last Updated:** January 2025  
**Version:** 1.0  
**Maintainer:** MenuMindAI Development Team

