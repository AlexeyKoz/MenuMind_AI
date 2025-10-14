# 🔍 MenuMine AI Frontend - Complete Analysis & Handoff Documentation

**Generated:** October 14, 2025  
**Purpose:** Comprehensive frontend codebase analysis for AI assistant handoff  
**Focus:** Integration of new backend features (multilingual support, IML enrichment, unit system)

---

## 1. 📋 PROJECT OVERVIEW

### Framework & Technology Stack
- **Framework:** React 18.3.1 with TypeScript 5.7.2
- **Build Tool:** Create React App (react-scripts 5.0.1)
- **Package Manager:** npm (based on package-lock.json presence)
- **Language:** TypeScript (strict mode enabled)
- **App Name:** MenuMind AI (previously referenced as MenuMine AI)
- **Description:** Smart family food intelligence platform

### Current Version
- **Frontend Version:** 0.1.0
- **React:** 18.3.1
- **TypeScript:** 5.7.2

### Key Characteristics
- ✅ TypeScript enabled (strict mode)
- ✅ Path aliases configured (`@/`, `@components/*`, etc.)
- ✅ No i18n library currently installed
- ✅ Single-page application (no React Router, custom page switching)
- ✅ WebSocket support for real-time features
- ⚠️ Zustand placeholder (not installed/used)

---

## 2. 📁 FOLDER STRUCTURE

```
frontend/
├── public/                        # Static assets
│   ├── index.html                # Main HTML template
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/               # ✅ Reusable UI components (15 files)
│   │   ├── CollaboratorManager.tsx
│   │   ├── DeleteConfirmationModal.tsx
│   │   ├── LeaveConfirmationModal.tsx
│   │   ├── LikeButton.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── LogToNutritionButton.tsx     # NEW: Logs recipe to nutrition
│   │   ├── Navigation.tsx
│   │   ├── NutritionSettings.tsx        # NEW: Nutrition preferences
│   │   ├── PrivateRoute.tsx
│   │   ├── RecipeBuilderWizard.tsx
│   │   ├── RecipeCard.tsx
│   │   ├── RecipeFinder.tsx
│   │   ├── ReviewsSection.tsx
│   │   ├── StarRating.tsx
│   │   └── index.ts                    # Component exports
│   │
│   ├── contexts/                 # ✅ React Context providers (2 contexts)
│   │   ├── AuthContext.tsx              # User authentication
│   │   ├── CollaborationContext.tsx     # Real-time WebSocket
│   │   └── index.ts
│   │
│   ├── pages/                    # ✅ Page components (13 pages)
│   │   ├── ArchivePage.tsx
│   │   ├── CanonicalRecipesPage.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Inventory.tsx
│   │   ├── Login.tsx
│   │   ├── NutritionTracker.tsx
│   │   ├── RecipeLibrary.tsx
│   │   ├── Recipes.tsx
│   │   ├── RecipesPage.tsx
│   │   ├── Registration.tsx
│   │   ├── SettingsPage.tsx             # ⚠️ Partial user preferences
│   │   ├── ShoppingList.tsx
│   │   └── index.ts
│   │
│   ├── services/                 # ✅ API & WebSocket services
│   │   ├── api.ts                       # Main API service class
│   │   ├── websocket.ts                 # Shopping list WebSocket
│   │   ├── userWebSocket.ts             # User-specific WebSocket
│   │   └── index.ts
│   │
│   ├── stores/                   # ⚠️ Zustand placeholder (disabled)
│   │   └── appStore.ts                  # Empty exports
│   │
│   ├── types/                    # ✅ TypeScript type definitions
│   │   └── index.ts                     # All types centralized
│   │
│   ├── utils/                    # ✅ Utility functions
│   │   ├── errorHandler.ts
│   │   ├── toast.ts
│   │   ├── unitConversion.ts            # ⚠️ Client-side unit conversion
│   │   ├── validation.ts
│   │   └── index.ts
│   │
│   ├── App.tsx                   # ✅ Main app component
│   ├── App.css                   # Global styles
│   ├── index.tsx                 # Entry point
│   ├── index.css                 # Tailwind imports
│   └── react-app-env.d.ts       # TypeScript declarations
│
├── build/                        # Production build output
├── node_modules/
├── package.json
├── package-lock.json
├── tsconfig.json                 # TypeScript configuration
├── tailwind.config.js            # Tailwind CSS config
├── postcss.config.js
├── Dockerfile.dev                # Development Docker
├── Dockerfile.prod               # Production Docker
├── nginx.conf                    # Production nginx config
└── README.md
```

---

## 3. 🔑 KEY DEPENDENCIES

### Core Framework
```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "typescript": "^5.7.2"
}
```

### UI & Styling
- **tailwindcss** `^3.4.0` - ✅ Utility-first CSS framework
- **lucide-react** `^0.544.0` - ✅ Icon library
- **react-hot-toast** `^2.6.0` - ✅ Toast notifications
- **autoprefixer** `^10.4.21` - CSS vendor prefixing
- **postcss** `^8.5.6` - CSS processing

### Routing & Navigation
- **react-router-dom** `^6.30.1` - ✅ INSTALLED but NOT USED
- **Custom page switching** - Uses state-based navigation instead

### HTTP Client & API
- **axios** `^1.7.9` - ✅ HTTP client (installed but not used extensively)
- **Custom fetch wrapper** - Uses native `fetch` in `api.ts`

### State Management
- **React Context API** - ✅ ACTIVE (AuthContext, CollaborationContext)
- **Zustand** - ❌ NOT INSTALLED (placeholder in appStore.ts)
- **Redux** - ❌ NOT INSTALLED

### i18n & Localization
- **react-i18next** - ❌ NOT INSTALLED
- **i18next** - ❌ NOT INSTALLED
- **Any i18n library** - ❌ NOT INSTALLED

### Forms
- **React Hook Form** - ❌ NOT INSTALLED
- **Formik** - ❌ NOT INSTALLED
- **Manual state management** - ✅ Used in all forms

### WebSocket
- **Native WebSocket API** - ✅ Used in websocket.ts and userWebSocket.ts
- **No WebSocket library** - Uses browser native implementation

### Testing
- **react-scripts** `5.0.1` - Includes Jest and Testing Library
- **No additional testing libraries**

### Build Tools
- **Create React App** - ✅ Standard CRA setup
- **No custom webpack config** - Using CRA defaults

---

## 4. 📦 EXISTING COMPONENTS

### 🎨 Layout Components
- **`Navigation.tsx`** - Top navigation bar with page switcher, user info, logout
  - Props: `currentPage`, `setCurrentPage`
  - Features: Page navigation, user display, partner indicator, logout button

### 🔐 Authentication Components
- **`PrivateRoute.tsx`** - Route protection wrapper (likely unused due to no router)

### 🛒 Shopping Components
- **`CollaboratorManager.tsx`** - Manage shopping list collaborators
  - Add collaborators by key
  - Update permissions
  - Real-time collaboration features
- **`DeleteConfirmationModal.tsx`** - Confirm list deletion with ownership transfer
- **`LeaveConfirmationModal.tsx`** - Confirm leaving a collaborative list

### 🍳 Recipe Components
- **`RecipeCard.tsx`** - Display recipe summary with social features
  - Shows: name, description, cuisine, difficulty, time, servings
  - Features: Like button, star rating, diet labels, source badge
  - **Missing:** Multilingual display, nutrition label, ingredient_key display
- **`RecipeFinder.tsx`** - Search and find recipes from web
- **`RecipeBuilderWizard.tsx`** - Step-by-step recipe creation wizard
- **`LikeButton.tsx`** - Like/unlike button with count
- **`StarRating.tsx`** - Display and input star ratings (1-5)
- **`ReviewsSection.tsx`** - Display and manage recipe reviews

### 🥗 Nutrition Components
- **`NutritionSettings.tsx`** - ✅ Configure nutrition tracking preferences
  - AI coach enable/disable
  - Data sharing permissions
  - Goal configuration (manual/AI)
  - Coaching preferences
- **`LogToNutritionButton.tsx`** - ✅ Log recipe/inventory to nutrition tracker

### 🔧 Utility Components
- **`LoadingSpinner.tsx`** - Loading indicator

### 📊 Component Status Summary
- **Total Components:** 15
- **Fully Implemented:** 13
- **Need Enhancement:** 2 (RecipeCard, Navigation)
- **Missing:** Language switcher, unit toggle, nutrition label component

---

## 5. 🌐 API INTEGRATION

### API Service Architecture

**Location:** `src/services/api.ts`

**Class Structure:**
```typescript
class ApiService {
    private token: string | null;
    private baseURL: string = 'http://localhost:8000/api';
    private onTokenExpired?: () => void;
    
    constructor(token: string | null, onTokenExpired?: () => void)
    
    // Generic HTTP methods
    get(endpoint: string): Promise<any>
    post(endpoint: string, data?: any): Promise<any>
    put(endpoint: string, data?: any): Promise<any>
    patch(endpoint: string, data?: any): Promise<any>
    delete(endpoint: string): Promise<any>
}
```

### Authentication Setup
```typescript
// Headers automatically added
headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${this.token}`,
    ...options.headers
}
```

### Base URL Configuration
- **Development:** `http://localhost:8000/api`
- **Hardcoded** - No environment variable
- ❌ **No .env file** present in frontend

### Token Management
- **Storage:** localStorage (`'token'`, `'refresh'`)
- **Retrieval:** From AuthContext
- **Expiration Handling:** 401 → logout callback
- **Refresh:** Not implemented

### Error Handling Pattern
```typescript
// 401 → Auto logout
if (response.status === 401) {
    this.onTokenExpired?.();
    throw new Error('Your session has expired');
}

// JSON error parsing
try {
    const errorData = JSON.parse(errorText);
    throw new Error(errorData.detail || errorData.error);
} catch {
    throw new Error(`API Error: ${response.statusText}`);
}
```

### API Endpoints Coverage

#### ✅ Shopping List (Fully Integrated)
```typescript
getShoppingLists()
createShoppingList(data)
deleteShoppingList(listId)
leaveList(listId)
getArchivedLists()
restoreList(listId)
permanentDeleteList(listId)
addItemToList(listId, data)
aiAddItems(listId, text)
toggleItem(itemId)
deleteItem(itemId)
updateWeightQuantity(itemId, weight_quantity)
updateLiquidQuantity(itemId, liquid_quantity)
mockStoreOrder(data)
addCollaborator(listId, data)
getCollaborators(listId)
updateCollaboratorPermissions(listId, data)
```

#### ✅ Inventory (Fully Integrated - Phase 5)
```typescript
getInventory()
getInventoryByLocation(location?)
getInventoryExpiringSoon(days?)
getInventoryLowStock()
getInventoryItem(id)
createInventoryItem(data)
updateInventoryItem(id, data)
deleteInventoryItem(id)
moveInventoryItem(id, newLocation)
getInventoryHistory(id)
bulkCreateInventory(items)
consumeInventory(items, recipeId?, notes?)
generateRecipesFromInventory(options?)
sendToInventory(listId, itemIds, aiCategorize?)
```

#### ✅ Nutrition Tracking (Fully Integrated)
```typescript
getNutritionSettings()
updateNutritionSettings(settings)
getNutritionGoals()
getNutritionEntries(params?)
createNutritionEntry(entry)
updateNutritionEntry(id, entry)
deleteNutritionEntry(id)
logFromRecipe(data)
logFromInventory(data)
getTodaySummary()
getWeeklySummary(weekStart?)
getMonthlySummary(month?)
getAISuggestions(params?)
askAICoach(question)
getAIWeeklyReport()
```

#### ✅ Recipes (Fully Integrated)
```typescript
getRecipes()
getRecipe(recipeId)
getMyRecipes()
getPopularRecipes()
getRecipeVersions(recipeId)
saveRecipe(recipeId, data?)
unsaveRecipe(recipeId)
getArchivedRecipes()
restoreRecipe(recipeId)
permanentlyDeleteRecipe(recipeId)
markRecipeCooked(recipeId)
findRecipe(query, shoppingListId?, addToList?)
downloadRCIP(recipeId, recipeName)
uploadRCIP(file)
```

#### ✅ Canonical Recipes (Phase 4 - Fully Integrated)
```typescript
getCanonicalRecipes(params?)  // search, cuisine, difficulty, diet_labels, etc.
getCanonicalRecipe(recipeId)
likeCanonicalRecipe(recipeId)
getLikeStatus(recipeId)
rateCanonicalRecipe(recipeId, rating)
addReview(recipeId, data)
getReviews(recipeId, params?)
updateReview(recipeId, reviewId, data)
deleteReview(recipeId, reviewId)
markReviewHelpful(recipeId, reviewId)
```

#### ✅ Recipe Builder (Phase 4)
```typescript
startBuilder()
builderStep(payload)  // steps: basic_info, ingredients, steps, review, finalize
```

#### ✅ User & Collaboration
```typescript
getMyCollaborationKey()
generateCollaborationKey()
updatePersonalColor(color)
```

#### ✅ Dashboard & Analytics
```typescript
getDashboardOverview(params?)
getAIInsights(params?)
regenerateAIInsights(period?)
getAchievements()
getAchievementsList()
getStreaks()
getCookingLogs()
logRecipeCooking(data)
```

#### ❌ NOT Integrated from Backend Handoff
- **UserPreferences API** - `/api/users/profile/preferences/`
  - `GET` - Fetch user preferences
  - `PATCH` - Update preferences (language, unit_system)
- **Multilingual recipe endpoints** - No specific calls for fetching recipes in user's language

### Request/Response Patterns

**Standard Request:**
```typescript
const api = new ApiService(token, handleLogout);
const data = await api.get('/recipes/recipes/');
```

**With Parameters:**
```typescript
const recipes = await api.getCanonicalRecipes({
    search: 'pasta',
    cuisine: 'italian',
    difficulty: 'easy',
    diet_labels: ['vegetarian'],
    sort: '-likes_count',
    page: 1
});
```

**Error Handling:**
```typescript
try {
    const result = await api.createInventoryItem(data);
    toast.success('Item created!');
} catch (error) {
    toast.error(error.message);
}
```

---

## 6. 🗺️ ROUTING STRUCTURE

### ⚠️ Unique Routing Implementation

**NOT using React Router!** Custom state-based page switching.

**Implementation Location:** `App.tsx`

```typescript
const [currentPage, setCurrentPage] = useState('shopping');

const pageComponents = {
    'dashboard': Dashboard,
    'shopping': ShoppingList,
    'nutrition': NutritionTracker,
    'recipes': Recipes,
    'discover': CanonicalRecipesPage,
    'inventory': Inventory,
    'archive': ArchivePage,
    'settings': SettingsPage
};

// URL sync (updates URL without full page reload)
useEffect(() => {
    if (user && currentPage) {
        const newUrl = `/${currentPage}`;
        window.history.pushState({ page: currentPage }, '', newUrl);
    }
}, [currentPage, user]);

// Render current page
const CurrentPageComponent = pageComponents[currentPage];
return <CurrentPageComponent />;
```

### Page Routes (URL Paths)

| URL Path | Component | Description | Status |
|----------|-----------|-------------|--------|
| `/` → `/shopping` | ShoppingList | Collaborative shopping lists | ✅ Implemented |
| `/dashboard` | Dashboard | Analytics and overview | ✅ Implemented |
| `/nutrition` | NutritionTracker | Nutrition tracking & AI coach | ✅ Implemented |
| `/recipes` | Recipes | User's saved recipes | ✅ Implemented |
| `/discover` | CanonicalRecipesPage | Discover canonical recipes | ✅ Implemented |
| `/inventory` | Inventory | Inventory management | ✅ Implemented |
| `/archive` | ArchivePage | Archived lists and recipes | ✅ Implemented |
| `/settings` | SettingsPage | User settings | ⚠️ Partial |
| `/login` | Login | Authentication | ✅ (shown when !user) |
| `/register` | Registration | User registration | ✅ (shown when !user) |

### Navigation Flow

```
App.tsx
├─ AuthProvider
│  └─ AppContent
│     ├─ if (!user) → Login/Registration
│     └─ if (user) → CollaborationProvider
│        ├─ Navigation (page switcher)
│        ├─ CurrentPageComponent
│        └─ Toaster
```

### ⚠️ Routing Limitations

1. **No deep linking** - Refreshing on `/nutrition` won't work properly (initializes to last valid page)
2. **No route parameters** - Uses query strings for IDs (e.g., `?id=123`)
3. **No nested routes** - Single-level pages only
4. **No lazy loading** - All page components loaded upfront
5. **No route guards** - Auth check in App.tsx only

### 🔄 Recommendation for IML Integration

**Suggestion:** Keep current routing system for now. Add language/unit system as:
- **URL query params:** `?lang=en&units=metric`
- **localStorage:** Persist user preference
- **Context:** Provide to all components

---

## 7. 🧠 STATE MANAGEMENT

### Primary Approach: **React Context API** ✅

**Two Active Contexts:**

#### 1. AuthContext (`contexts/AuthContext.tsx`)

**Purpose:** User authentication and session management

**State:**
```typescript
interface AuthContextType {
    user: User | null;              // Current authenticated user
    token: string | null;           // JWT access token
    loading: boolean;               // Initial auth check
    login: (username, password) => Promise<{success, error?}>;
    register: (username, email, password, firstName, lastName) => Promise<{success, error?}>;
    logout: () => void;
}
```

**User Data Structure:**
```typescript
interface User {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    partner?: User;                 // Linked partner for family account
    daily_calories_goal: number;
    daily_protein_goal: number;
    daily_carbs_goal: number;
    daily_fat_goal: number;
}
```

**Storage:**
- ✅ **localStorage:** `token`, `refresh`
- ✅ **Memory:** user object (from API)
- ❌ **Missing:** `preferred_language`, `unit_system` in user object

**Usage Pattern:**
```typescript
const { user, token, login, logout } = useAuth();

// Access user data
console.log(user?.username);
console.log(user?.daily_calories_goal);

// Perform auth actions
await login(username, password);
logout();
```

**API Fetch:** Calls `/api/users/profile/` on mount to load user

#### 2. CollaborationContext (`contexts/CollaborationContext.tsx`)

**Purpose:** Real-time WebSocket collaboration for shopping lists

**State:**
```typescript
interface CollaborationContextType {
    ws: WebSocket | null;
    connectionStatus: 'connecting' | 'connected' | 'disconnected';
    activeCollaborators: Map<string, Collaborator>;
    typingIndicators: Map<string, TypingInfo>;
    joinList: (listId: string) => void;
    leaveList: () => void;
    sendMessage: (type: string, data: any) => void;
    // ... more methods
}
```

**Features:**
- WebSocket connection management
- Real-time collaborator presence
- Typing indicators
- Live shopping list updates
- Automatic reconnection

**Usage:**
```typescript
const { ws, activeCollaborators, joinList, leaveList } = useCollaboration();

// Join a list
joinList(listId);

// Access active users
activeCollaborators.forEach(collaborator => {
    console.log(collaborator.username, collaborator.color);
});

// Leave when done
leaveList();
```

### Secondary Approach: **Local Component State** ✅

**Pattern:** `useState` for page-specific data

**Example (ShoppingList):**
```typescript
const [lists, setLists] = useState<ShoppingList[]>([]);
const [selectedList, setSelectedList] = useState<string | null>(null);
const [newItemName, setNewItemName] = useState('');
const [loading, setLoading] = useState(true);
```

**Example (NutritionTracker):**
```typescript
const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
const [selectedMealType, setSelectedMealType] = useState<'breakfast' | 'lunch' | 'dinner' | 'snack'>('breakfast');
const [nutritionSettings, setNutritionSettings] = useState<UserNutritionSettings | null>(null);
```

### ⚠️ Zustand (Disabled/Placeholder)

**Status:** NOT INSTALLED, placeholder only

**File:** `src/stores/appStore.ts`

```typescript
// Empty exports to prevent import errors
export const useAppStore = () => ({});
export const useSidebarState = () => ({ 
    sidebarOpen: false, 
    toggleSidebar: () => {} 
});
```

**Recommendation:** If global state needed for language/units, can install Zustand:
```bash
npm install zustand
```

### 🔄 State Flow Diagram

```
┌─────────────────────────────────────────┐
│           App.tsx (Root)                │
│  ┌─────────────────────────────────┐   │
│  │     AuthProvider (Global)       │   │
│  │  - user, token, login, logout   │   │
│  │  - Persists to localStorage     │   │
│  └──────────┬──────────────────────┘   │
│             │                            │
│  ┌──────────▼──────────────────────┐   │
│  │   CollaborationProvider          │   │
│  │  - WebSocket connection          │   │
│  │  - Real-time list updates        │   │
│  └──────────┬──────────────────────┘   │
│             │                            │
│  ┌──────────▼──────────────────────┐   │
│  │   Current Page Component         │   │
│  │  - Local useState for page data  │   │
│  │  - API calls via ApiService      │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### ❌ What's NOT Implemented

1. **Global language/unit preferences** - No context for this yet
2. **Redux** - Not used
3. **Zustand** - Not installed (just placeholder)
4. **MobX** - Not used
5. **Recoil** - Not used

### 🎯 Recommendations for IML Integration

**Option 1: Extend AuthContext** (Simplest)
```typescript
// Add to AuthContext
interface User {
    // ... existing fields
    preferred_language?: 'en' | 'ru' | 'he';
    unit_system?: 'metric' | 'imperial';
}
```

**Option 2: Create PreferencesContext** (Better separation)
```typescript
interface PreferencesContext {
    language: 'en' | 'ru' | 'he';
    unitSystem: 'metric' | 'imperial';
    setLanguage: (lang) => void;
    setUnitSystem: (system) => void;
}
```

**Option 3: Install Zustand** (Most flexible)
```typescript
const usePreferencesStore = create((set) => ({
    language: 'en',
    unitSystem: 'metric',
    setLanguage: (lang) => set({ language: lang }),
    setUnitSystem: (system) => set({ unitSystem: system })
}));
```

---

## 8. 🎨 STYLING APPROACH

### Primary: **Tailwind CSS** ✅

**Config Location:** `tailwind.config.js`

```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {},  // Using default Tailwind theme
  },
  plugins: [],   // No additional plugins
}
```

**Usage Pattern:**
```tsx
// Inline Tailwind classes (most common pattern)
<div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300">
    <h3 className="text-2xl font-bold mb-2 text-gray-900">
        Title
    </h3>
    <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
        Click Me
    </button>
</div>
```

**Import Location:** `src/index.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Secondary: **Custom CSS** (Minimal)

**Global Styles:** `src/App.css`
- Minimal custom styles
- Mostly using Tailwind utilities

### 🎨 Design System (Implicit)

**Color Palette (from code analysis):**
- **Primary:** Blue gradient (`from-blue-500 to-purple-600`)
- **Secondary:** Green (`from-green-600 to-blue-600` in nav)
- **Success:** Green-500
- **Error:** Red-500
- **Warning:** Yellow-100/800
- **Neutral:** Gray scale (50, 100, 200, ... 900)

**Common Patterns:**
```tsx
// Cards
className="bg-white rounded-xl shadow-md p-6"

// Buttons (Primary)
className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"

// Buttons (Secondary)
className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg"

// Inputs
className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"

// Badges/Tags
className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
```

### Typography
- **Default Font:** System fonts (no custom fonts)
- **Font Sizes:** Tailwind defaults (text-xs to text-6xl)
- **Font Weights:** normal, medium, semibold, bold

### Responsive Design

**Approach:** Tailwind responsive prefixes

```tsx
// Mobile-first breakpoints
className="text-sm md:text-base lg:text-lg"           // Responsive text
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3"  // Responsive grid
className="hidden md:block"                           // Hide on mobile
className="block md:hidden"                           // Show only on mobile
```

**Breakpoints (Tailwind defaults):**
- `sm:` 640px
- `md:` 768px
- `lg:` 1024px
- `xl:` 1280px
- `2xl:` 1536px

### Icons

**Library:** Lucide React `^0.544.0`

```tsx
import { Heart, Star, Clock, Users } from 'lucide-react';

<Heart className="w-5 h-5 text-red-500" />
```

**Also uses:** Emoji icons (🛒, 📊, 🥗, 👨‍🍳, etc.) in Navigation

### 🌓 Dark Mode
- ❌ **NOT IMPLEMENTED**
- No theme toggle
- No dark mode classes

### 🌍 RTL Support
- ❌ **NOT IMPLEMENTED**
- No RTL-specific styles
- **Critical for Hebrew (`he`)** language support

### ⚠️ Styling Gaps for IML Integration

1. **No RTL support** - Required for Hebrew
2. **No theme system** - Language-specific themes not possible
3. **No CSS-in-JS** - Can't dynamically switch styles based on language
4. **Hardcoded text sizes** - May not work well with longer translations

---

## 9. 🌐 INTERNATIONALIZATION (i18n)

### ❌ Current Status: **NOT IMPLEMENTED**

**No i18n library installed:**
- ❌ react-i18next
- ❌ i18next
- ❌ react-intl
- ❌ formatjs

**All text is hardcoded in English:**
```tsx
// Example from Navigation.tsx
const navItems = [
    { id: 'shopping', label: 'Shopping', icon: '🛒' },
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'nutrition', label: 'Nutrition', icon: '🥗' },
    // ... all English
];
```

### ⚠️ Partial Language Support

**SettingsPage.tsx has language dropdown:**
```tsx
const languages = [
    { value: 'en', label: 'English' },
    { value: 'he', label: 'Hebrew' },
    { value: 'ru', label: 'Russian' }
];

<select value={formData.preferred_language || 'en'}>
    {languages.map(lang => (
        <option value={lang.value}>{lang.label}</option>
    ))}
</select>
```

**BUT:**
- ✅ Dropdown exists
- ✅ Can save to backend (`preferred_language` field)
- ❌ No effect on UI (all text still English)
- ❌ No translation files
- ❌ No translation function

### 📂 Translation Files Structure (Recommended)

**Suggested structure if implementing i18n:**
```
src/
└── locales/
    ├── en.json       # English translations
    ├── ru.json       # Russian translations
    └── he.json       # Hebrew translations
```

**Example content:**
```json
// en.json
{
  "nav": {
    "shopping": "Shopping",
    "dashboard": "Dashboard",
    "nutrition": "Nutrition"
  },
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete"
  }
}
```

### 🔄 How to Add i18n (Recommended Approach)

**Step 1: Install react-i18next**
```bash
npm install react-i18next i18next i18next-browser-languagedetector
```

**Step 2: Create translation files**
```
src/locales/en.json
src/locales/ru.json
src/locales/he.json
```

**Step 3: Initialize i18next**
```typescript
// src/i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import ru from './locales/ru.json';
import he from './locales/he.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ru: { translation: ru },
      he: { translation: he }
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
```

**Step 4: Usage in components**
```tsx
import { useTranslation } from 'react-i18next';

const Navigation = () => {
    const { t, i18n } = useTranslation();
    
    return (
        <nav>
            <button>{t('nav.shopping')}</button>
            <button onClick={() => i18n.changeLanguage('ru')}>
                Switch to Russian
            </button>
        </nav>
    );
};
```

### 🔄 Syncing with Backend UserPreferences

**After implementing i18n, sync with backend:**
```typescript
// Fetch user language preference
const prefs = await api.get('/users/profile/preferences/');
i18n.changeLanguage(prefs.preferred_language);

// Update when user changes
const updateLanguage = async (lang: string) => {
    await api.patch('/users/profile/preferences/', {
        preferred_language: lang
    });
    i18n.changeLanguage(lang);
};
```

### ⚠️ RTL Support for Hebrew

**Must add Tailwind RTL plugin:**
```bash
npm install tailwindcss-rtl
```

**Update tailwind.config.js:**
```javascript
module.exports = {
  plugins: [
    require('tailwindcss-rtl')
  ]
}
```

**Usage:**
```tsx
<div className="text-left rtl:text-right">
    Content that switches direction
</div>
```

### 📊 i18n Implementation Status

| Feature | Status | Priority |
|---------|--------|----------|
| i18n library | ❌ Not installed | 🔴 Critical |
| Translation files | ❌ Don't exist | 🔴 Critical |
| Language switcher | ⚠️ UI exists, no function | 🔴 Critical |
| Fetch user language | ❌ Not fetching | 🔴 Critical |
| RTL support | ❌ Not implemented | 🟠 High (for Hebrew) |
| Date/number formatting | ❌ Not implemented | 🟡 Medium |

---

## 10. 🔐 AUTHENTICATION & USER CONTEXT

### Authentication Flow

```
┌──────────────────────────────────────┐
│     User visits app                  │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  AuthContext checks localStorage     │
│  token = localStorage.getItem('token')│
└──────────┬───────────────────────────┘
           │
      ┌────┴────┐
      │  Token? │
      └────┬────┘
           │
    ┌──────┴──────┐
    │             │
   YES            NO
    │             │
    │             ▼
    │      ┌─────────────────┐
    │      │  Show Login or  │
    │      │  Registration   │
    │      └─────────────────┘
    │             │
    │             ▼
    │      ┌─────────────────┐
    │      │ POST /api/users/│
    │      │ auth/login/     │
    │      └─────────────────┘
    │             │
    ▼             │
┌──────────────────────────────────────┐
│  GET /api/users/profile/             │
│  Fetch user data with token          │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  setUser(data)                       │
│  User authenticated ✅                │
│  Show main app                       │
└──────────────────────────────────────┘
```

### User Data Storage

**AuthContext (`contexts/AuthContext.tsx`):**

```typescript
interface User {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    partner?: User;                     // Family account linking
    daily_calories_goal: number;
    daily_protein_goal: number;
    daily_carbs_goal: number;
    daily_fat_goal: number;
    // ❌ MISSING: preferred_language, unit_system
}

// State
const [user, setUser] = useState<User | null>(null);
const [token, setToken] = useState<string | null>(
    localStorage.getItem('token')
);
const [loading, setLoading] = useState(true);
```

**Storage Locations:**

1. **localStorage:**
   - ✅ `'token'` - JWT access token
   - ✅ `'refresh'` - JWT refresh token
   - ❌ NO user preferences cached

2. **Memory (React state):**
   - ✅ `user` object (from API)
   - ✅ Re-fetched on every page reload

3. **NOT STORED:**
   - ❌ User language preference
   - ❌ Unit system preference
   - ❌ Theme preference

### Accessing Current User in Components

**Pattern 1: useAuth Hook (Most Common)**
```typescript
import { useAuth } from '../contexts/AuthContext';

const MyComponent = () => {
    const { user, token, logout } = useAuth();
    
    // Access user data
    console.log(user?.username);
    console.log(user?.email);
    console.log(user?.daily_calories_goal);
    
    // Check if user is logged in
    if (!user) {
        return <div>Please log in</div>;
    }
    
    return <div>Welcome, {user.first_name}!</div>;
};
```

**Pattern 2: Direct Context (Rare)**
```typescript
import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

const { user, token } = useContext(AuthContext);
```

**Pattern 3: Token for API Calls**
```typescript
const { token, logout } = useAuth();
const api = useMemo(
    () => new ApiService(token, logout), 
    [token, logout]
);

// Use api for requests
const data = await api.getRecipes();
```

### Authentication Methods

#### Login
```typescript
const { login } = useAuth();

const handleLogin = async () => {
    const result = await login(username, password);
    if (result.success) {
        // Auto-reload page to show authenticated view
        window.location.reload();
    } else {
        toast.error(result.error);
    }
};
```

#### Registration
```typescript
const { register } = useAuth();

const handleRegister = async () => {
    const result = await register(
        username, 
        email, 
        password, 
        firstName, 
        lastName
    );
    if (result.success) {
        window.location.reload();
    } else {
        toast.error(result.error);
    }
};
```

#### Logout
```typescript
const { logout } = useAuth();

const handleLogout = () => {
    logout();  // Clears localStorage, sets user to null
    // App.tsx will auto-show login screen
};
```

### Token Expiration Handling

**Automatic logout on 401:**
```typescript
// ApiService constructor
const api = new ApiService(token, () => {
    console.log('🔐 Token expired - logging out');
    alert('Your session has expired. Please log in again.');
    logout();
});

// API service checks response
if (response.status === 401) {
    this.onTokenExpired?.();  // Calls logout callback
    throw new Error('Your session has expired');
}
```

**⚠️ Token Refresh NOT Implemented**
- Backend provides `refresh` token
- Stored in localStorage
- ❌ **Never used** - no refresh logic

### UserPreferences Integration Status

#### ❌ NOT Implemented (from Backend Handoff)

**Backend provides:**
```python
# UserPreferences model
class UserPreferences(models.Model):
    user: OneToOneField
    preferred_language: str (en, ru, he)
    unit_system: str (metric, imperial)
    timezone: str
    date_format: str
    # ... more fields
```

**API Endpoints Available:**
- `GET /api/users/profile/preferences/` - Fetch preferences
- `PATCH /api/users/profile/preferences/` - Update preferences

**Frontend Status:**
- ❌ NOT fetching preferences on login
- ❌ NOT storing in context/state
- ❌ NOT using preferred_language for UI
- ❌ NOT using unit_system for conversions
- ⚠️ SettingsPage has dropdown but doesn't integrate

### 🎯 Required Implementation

**Step 1: Update User Type**
```typescript
interface User {
    // ... existing fields
    preferred_language?: 'en' | 'ru' | 'he';
    unit_system?: 'metric' | 'imperial';
}
```

**Step 2: Fetch Preferences on Login**
```typescript
const fetchUserProfile = async () => {
    try {
        // Existing call
        const profileData = await fetch('/api/users/profile/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        // NEW: Fetch preferences
        const prefsData = await fetch('/api/users/profile/preferences/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const prefs = await prefsData.json();
        setUser({
            ...profile,
            preferred_language: prefs.preferred_language,
            unit_system: prefs.unit_system
        });
    } catch (error) {
        console.error('Profile fetch error:', error);
    }
};
```

**Step 3: Use in Components**
```typescript
const { user } = useAuth();
const currentLanguage = user?.preferred_language || 'en';
const currentUnitSystem = user?.unit_system || 'metric';

// Use for i18n
i18n.changeLanguage(currentLanguage);

// Use for unit conversion
const displayAmount = convertUnit(amount, unit, currentUnitSystem);
```

### 🔄 User Preferences Flow Diagram

```
┌─────────────────────────────────────┐
│  User logs in                       │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Fetch /api/users/profile/          │
│  Fetch /api/users/profile/preferences/  ❌ NOT DONE
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Store in AuthContext               │
│  - user.preferred_language          ❌ NOT STORED
│  - user.unit_system                 ❌ NOT STORED
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Apply to UI                        │
│  - i18n.changeLanguage(lang)        ❌ NOT DONE
│  - Use unit_system for conversions  ❌ NOT DONE
└─────────────────────────────────────┘
```

---

## 11. 🔌 EXISTING BACKEND INTEGRATION

### ✅ Fully Integrated Features

#### 1. **Shopping Lists** (Phase 1)
- ✅ CRUD operations
- ✅ Real-time collaboration (WebSocket)
- ✅ Collaborator management
- ✅ Archive and restore
- ✅ Permanent deletion with ownership transfer
- ✅ AI-powered item addition

#### 2. **Inventory Management** (Phase 5)
- ✅ Full CRUD operations
- ✅ Location-based organization (fridge, freezer, pantry, counter)
- ✅ Expiration tracking (urgent, warning, ok)
- ✅ Low stock alerts
- ✅ Bulk creation from shopping list
- ✅ AI categorization integration
- ✅ Recipe generation from inventory
- ✅ Consumption tracking with history

#### 3. **Nutrition Tracking** (Phase 6)
- ✅ Daily nutrition logging
- ✅ Meal tracking (breakfast, lunch, dinner, snack)
- ✅ Nutrition goals (manual/AI-calculated)
- ✅ Weekly/monthly summaries
- ✅ AI coach integration (enable/disable)
- ✅ Log from recipe
- ✅ Log from inventory
- ✅ Nutrition settings UI component

#### 4. **Recipes** (Phases 2-4)
- ✅ Recipe discovery (canonical recipes)
- ✅ Recipe search and filtering
- ✅ Like/rating system
- ✅ Reviews and ratings
- ✅ Recipe builder wizard
- ✅ RCIP upload/download
- ✅ Recipe versioning
- ✅ Fork and save recipes
- ✅ Mark as cooked
- ✅ Web scraping and AI conversion

#### 5. **Dashboard & Analytics** (Phase 7)
- ✅ Dashboard overview
- ✅ AI insights
- ✅ Achievements
- ✅ Streaks
- ✅ Cooking logs

#### 6. **User Management**
- ✅ Authentication (login/register)
- ✅ User profile
- ✅ Partner linking (family accounts)
- ✅ Personal color for collaboration
- ✅ Collaboration keys

### ⚠️ Partially Integrated Features

#### 1. **User Settings** (SettingsPage.tsx)
- ✅ Basic profile editing (name, email)
- ✅ Nutrition goals
- ✅ Activity level
- ✅ Dietary restrictions
- ✅ Language dropdown UI
- ⚠️ **Language selection exists but doesn't affect UI**
- ⚠️ **Unit preferences exist but not used**
- ❌ NO preferences API integration (`/api/users/profile/preferences/`)

#### 2. **Recipe Display**
- ✅ Recipe metadata (name, description, cuisine, etc.)
- ✅ Ingredients list
- ✅ Steps display
- ❌ **NO multilingual title display** (title_translations not used)
- ❌ **NO multilingual description** (description_translations not used)
- ❌ **NO translated steps** (steps_translations not used)
- ❌ **NO nutrition label** (nutrition_per_serving not prominently displayed)
- ❌ **NO source badge** (IML vs AI vs default)

---

## 12. ❌ MISSING FEATURES (from Backend Handoff)

### Priority 🔴 Critical Features

#### 1. **Language Switcher Component** ❌
**Backend Ready:** ✅ UserPreferences.preferred_language, title_translations, etc.

**What's Missing:**
- Component to switch language in Navigation or Settings
- Fetch user's preferred_language from API
- Store in context/state
- Apply to entire UI with i18n library
- Persist to backend on change

**Implementation Steps:**
```typescript
// 1. Install i18next
npm install react-i18next i18next i18next-browser-languagedetector

// 2. Create LanguageSwitcher component
const LanguageSwitcher = () => {
    const { i18n } = useTranslation();
    const { user } = useAuth();
    const api = new ApiService(token);
    
    const changeLanguage = async (lang: string) => {
        await i18n.changeLanguage(lang);
        await api.patch('/users/profile/preferences/', {
            preferred_language: lang
        });
    };
    
    return (
        <select value={i18n.language} onChange={(e) => changeLanguage(e.target.value)}>
            <option value="en">🇬🇧 English</option>
            <option value="ru">🇷🇺 Русский</option>
            <option value="he">🇮🇱 עברית</option>
        </select>
    );
};

// 3. Add to Navigation.tsx
<LanguageSwitcher />
```

#### 2. **Unit System Toggle** ❌
**Backend Ready:** ✅ UserPreferences.unit_system, unit conversion utilities

**What's Missing:**
- Toggle between metric/imperial
- Display in Navigation or Settings
- Apply to all ingredient quantities
- Show both units with alternatives (e.g., "300g (10.6 oz)")
- Persist to backend

**Implementation:**
```typescript
const UnitToggle = () => {
    const [unitSystem, setUnitSystem] = useState<'metric' | 'imperial'>('metric');
    const api = new ApiService(token);
    
    const toggle = async () => {
        const newSystem = unitSystem === 'metric' ? 'imperial' : 'metric';
        setUnitSystem(newSystem);
        await api.patch('/users/profile/preferences/', {
            unit_system: newSystem
        });
    };
    
    return (
        <button onClick={toggle}>
            {unitSystem === 'metric' ? '⚖️ Metric' : '⚖️ Imperial'}
        </button>
    );
};
```

#### 3. **Multilingual Recipe Display** ❌
**Backend Provides:**
- `title_translations: {en: "...", ru: "...", he: "..."}`
- `description_translations`
- `steps_translations`

**Current:** Only shows original title/description

**Needed:**
```typescript
const RecipeDisplay = ({ recipe }) => {
    const { i18n } = useTranslation();
    const lang = i18n.language;
    
    // Use translated title if available
    const title = recipe.title_translations?.[lang] || recipe.name;
    const description = recipe.description_translations?.[lang] || recipe.description;
    const steps = recipe.steps_translations?.[lang] || recipe.steps;
    
    return (
        <div>
            <h1>{title}</h1>
            <p>{description}</p>
            {steps.map((step, i) => (
                <p key={i}>{step}</p>
            ))}
        </div>
    );
};
```

#### 4. **UserPreferences API Integration** ❌
**Backend Endpoints:**
- `GET /api/users/profile/preferences/`
- `PATCH /api/users/profile/preferences/`

**Missing:**
- Fetch on login
- Store in AuthContext or PreferencesContext
- Use throughout app
- Update on settings change

**Add to api.ts:**
```typescript
// In ApiService class
getUserPreferences = () => 
    this.request('/users/profile/preferences/');

updateUserPreferences = (prefs: Partial<UserPreferences>) =>
    this.request('/users/profile/preferences/', {
        method: 'PATCH',
        body: JSON.stringify(prefs)
    });
```

### Priority 🟠 High Features

#### 5. **Nutrition Label Component** ❌
**Backend Provides:** `nutrition_per_serving` with calories, protein, carbs, fat, etc.

**Missing:** Prominent display component

**Needed:**
```typescript
const NutritionLabel = ({ nutrition }) => (
    <div className="border-2 border-black p-4">
        <h3 className="font-bold text-xl">Nutrition Facts</h3>
        <div className="border-t-4 border-black mt-1 pt-1">
            <div>Calories: <b>{nutrition.calories}</b></div>
            <div>Protein: {nutrition.protein}g</div>
            <div>Carbs: {nutrition.carbs}g</div>
            <div>Fat: {nutrition.fat}g</div>
        </div>
    </div>
);
```

#### 6. **Source Badges (IML/AI/Default)** ❌
**Backend Provides:**
- `ingredient_key` (if from IML)
- `source: 'iml' | 'ai' | 'default'`
- `confidence: 0.0-1.0`

**Missing:** Visual indicators

**Needed:**
```typescript
const SourceBadge = ({ source, confidence }) => {
    const badges = {
        iml: { label: 'IML', color: 'bg-green-100 text-green-800', icon: '✅' },
        ai: { label: 'AI', color: 'bg-blue-100 text-blue-800', icon: '🤖' },
        default: { label: 'Rule', color: 'bg-gray-100 text-gray-800', icon: '📋' }
    };
    
    const badge = badges[source];
    
    return (
        <span className={`px-2 py-1 rounded text-xs ${badge.color}`}>
            {badge.icon} {badge.label} ({(confidence * 100).toFixed(0)}%)
        </span>
    );
};
```

#### 7. **RTL Support for Hebrew** ❌
**Required for:** Hebrew (`he`) language

**Missing:**
- Tailwind RTL plugin
- RTL-specific layouts
- Direction switching based on language

**Implementation:**
```bash
npm install tailwindcss-rtl
```

```javascript
// tailwind.config.js
module.exports = {
  plugins: [require('tailwindcss-rtl')]
}
```

```tsx
// App.tsx
<div className={i18n.language === 'he' ? 'rtl' : 'ltr'}>
    <Navigation />
    <Content />
</div>
```

### Priority 🟡 Medium Features

#### 8. **Ingredient Alternatives Display** ❌
**Backend Provides:**
```json
{
  "alternatives": {
    "metric": "300g",
    "imperial": "10.6 oz"
  }
}
```

**Needed:** Show both units

```typescript
const IngredientDisplay = ({ ingredient, userUnitSystem }) => {
    const primary = userUnitSystem === 'metric' 
        ? ingredient.alternatives.metric 
        : ingredient.alternatives.imperial;
    const secondary = userUnitSystem === 'metric'
        ? ingredient.alternatives.imperial
        : ingredient.alternatives.metric;
    
    return (
        <li>
            {ingredient.name}: <b>{primary}</b> 
            <span className="text-gray-500 text-sm"> ({secondary})</span>
        </li>
    );
};
```

#### 9. **Enhanced Recipe Card** ❌
**Current:** Basic recipe display

**Backend Provides:**
- Multilingual titles
- Nutrition data
- IML enrichment status
- Coverage percentage

**Needed:** Update RecipeCard component to use all new data

#### 10. **Settings Page Enhancement** ⚠️
**Current:** Basic settings

**Needed:**
- Integrate UserPreferences API
- Add more preference controls
- Visual feedback on save
- Sync with backend properly

---

## 13. 📝 CODE PATTERNS & CONVENTIONS

### Component Structure

**Pattern:** Functional Components with Hooks ✅

```typescript
// Standard component pattern
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';

interface ComponentNameProps {
    prop1: string;
    prop2?: number;
}

const ComponentName: React.FC<ComponentNameProps> = ({ prop1, prop2 }) => {
    // 1. Hooks first
    const { user, token } = useAuth();
    const [state, setState] = useState<Type>(initialValue);
    
    // 2. useMemo/useCallback
    const api = useMemo(() => new ApiService(token), [token]);
    
    // 3. useEffect
    useEffect(() => {
        fetchData();
    }, []);
    
    // 4. Event handlers
    const handleClick = async () => {
        try {
            await api.doSomething();
            toast.success('Success!');
        } catch (error) {
            toast.error(error.message);
        }
    };
    
    // 5. Render
    return (
        <div className="container">
            {/* JSX */}
        </div>
    );
};

export default ComponentName;
```

**NOT USED:**
- ❌ Class components
- ❌ Higher-Order Components (HOCs)
- ❌ Render props pattern

### Props Naming Conventions

**Pattern:** camelCase ✅

```typescript
interface Props {
    userName: string;           // ✅ camelCase
    onItemClick: () => void;    // ✅ on + Action
    isLoading: boolean;         // ✅ is/has for booleans
    totalCount: number;
    selectedItem?: Item;        // ✅ ? for optional
}
```

**Event Handler Props:**
- `onClick`, `onChange`, `onSubmit`, etc.
- `onItemClick`, `onUserSelect` (specific actions)
- Always start with `on`

### File Naming Conventions

**Pattern:** PascalCase for components, camelCase for utilities ✅

```
src/
├── components/
│   ├── RecipeCard.tsx         ✅ PascalCase
│   ├── ShoppingList.tsx       ✅ PascalCase
│   └── NutritionSettings.tsx  ✅ PascalCase
├── pages/
│   ├── Dashboard.tsx          ✅ PascalCase
│   └── SettingsPage.tsx       ✅ PascalCase
├── services/
│   ├── api.ts                 ✅ camelCase
│   └── websocket.ts           ✅ camelCase
├── utils/
│   ├── errorHandler.ts        ✅ camelCase
│   └── unitConversion.ts      ✅ camelCase
└── contexts/
    └── AuthContext.tsx        ✅ PascalCase
```

### Error Handling

**Pattern 1: Try-Catch with Toast** (Most common)

```typescript
const handleAction = async () => {
    try {
        setLoading(true);
        const result = await api.doSomething(data);
        toast.success('Action completed!');
        // Update state
        setData(result);
    } catch (error) {
        console.error('Action failed:', error);
        toast.error(error.message || 'Something went wrong');
    } finally {
        setLoading(false);
    }
};
```

**Pattern 2: Result Object** (Auth only)

```typescript
const handleLogin = async () => {
    const result = await login(username, password);
    if (result.success) {
        window.location.reload();
    } else {
        toast.error(result.error);
    }
};
```

**Error Logging:**
- ✅ `console.error()` for errors
- ✅ `console.log()` for debug
- ❌ No error tracking service (Sentry, etc.)

### Loading States Pattern

**Standard Pattern:**

```typescript
const [loading, setLoading] = useState(true);
const [data, setData] = useState<Type[]>([]);

useEffect(() => {
    const fetchData = async () => {
        try {
            setLoading(true);
            const result = await api.getData();
            setData(result);
        } catch (error) {
            toast.error('Failed to load data');
        } finally {
            setLoading(false);
        }
    };
    
    fetchData();
}, []);

if (loading) {
    return <LoadingSpinner />;
}

return <DataDisplay data={data} />;
```

**Components with Loading States:**
- LoadingSpinner component
- Inline loading text ("Loading...")
- Disabled buttons during action

### Async Operations

**Pattern:** Always async/await, never .then() ✅

```typescript
// ✅ Good
const data = await api.getData();

// ❌ Never used
api.getData().then(data => { ... });
```

### TypeScript Usage

**Patterns:**

1. **Interface for props:**
```typescript
interface Props {
    item: Item;
    onSelect: (id: string) => void;
}
```

2. **Type for state:**
```typescript
const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
```

3. **Imported types:**
```typescript
import { User, ShoppingList } from '../types';
```

4. **Inline types (rare):**
```typescript
const [data, setData] = useState<{ name: string; count: number }[]>([]);
```

**Type Safety:**
- ✅ Strict mode enabled
- ✅ No `any` types (mostly)
- ✅ Optional chaining (`user?.name`)
- ✅ Nullish coalescing (`value ?? defaultValue`)

### Conditional Rendering

**Pattern 1: Early Return**
```typescript
if (!user) {
    return <Login />;
}

return <Dashboard />;
```

**Pattern 2: Ternary**
```typescript
{loading ? <LoadingSpinner /> : <Content />}
{user?.partner && <PartnerIndicator />}
```

**Pattern 3: Logical AND**
```typescript
{showModal && <Modal />}
{error && <ErrorMessage />}
```

### Code Organization

**Import Order:**
```typescript
// 1. React
import React, { useState, useEffect } from 'react';

// 2. Third-party libraries
import { toast } from 'react-hot-toast';

// 3. Local imports
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import RecipeCard from '../components/RecipeCard';
import { Recipe } from '../types';

// 4. Styles (if any)
import './styles.css';
```

**Function Order in Component:**
```typescript
const Component = () => {
    // 1. Hooks
    // 2. useMemo/useCallback
    // 3. useEffect
    // 4. Event handlers
    // 5. Helper functions
    // 6. Render logic
    // 7. Return JSX
};
```

---

## 14. 🌍 ENVIRONMENT & CONFIGURATION

### Environment Variables

**Status:** ❌ NO .env file in frontend

**Hardcoded Values:**
```typescript
// src/services/api.ts
private baseURL: string = 'http://localhost:8000/api';  // ❌ Hardcoded

// src/contexts/AuthContext.tsx
const response = await fetch('http://localhost:8000/api/users/profile/', {
    // ❌ Hardcoded
});
```

**Recommended .env Structure:**
```env
# Frontend .env (should be created)
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENV=development

# Optional
REACT_APP_ENABLE_DEBUG=true
REACT_APP_VERSION=0.1.0
```

**Usage Pattern:**
```typescript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

### Configuration Files

#### 1. **TypeScript Configuration** (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,                         // ✅ Strict mode
    "jsx": "react-jsx",                     // ✅ New JSX transform
    "module": "esnext",
    "moduleResolution": "node",
    "baseUrl": "src",                       // ✅ Absolute imports from src/
    "paths": {                              // ✅ Path aliases
      "@/*": ["*"],
      "@components/*": ["components/*"],
      "@services/*": ["services/*"],
      "@hooks/*": ["hooks/*"],
      "@types/*": ["types/*"]
    }
  }
}
```

**Path Alias Usage:**
```typescript
// ✅ Can use
import RecipeCard from '@components/RecipeCard';
import { User } from '@types/index';

// ✅ Also can use (currently used)
import RecipeCard from '../components/RecipeCard';
```

#### 2. **Tailwind Configuration** (`tailwind.config.js`)

```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],  // ✅ Scan all source files
  theme: {
    extend: {},  // ❌ No custom theme extensions
  },
  plugins: [],   // ❌ No plugins (needs RTL plugin)
}
```

#### 3. **PostCSS Configuration** (`postcss.config.js`)

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### API Base URL Setup

**Current Implementation:**
```typescript
// src/services/api.ts
class ApiService {
    private baseURL: string = 'http://localhost:8000/api';  // ❌ Hardcoded
}
```

**Recommended Update:**
```typescript
class ApiService {
    private baseURL: string = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
}
```

### Feature Flags

**Status:** ❌ NOT IMPLEMENTED

**Could be useful for:**
- Gradual rollout of i18n
- A/B testing unit toggle UI
- Beta features

**Suggested Implementation:**
```typescript
// config/featureFlags.ts
export const FEATURE_FLAGS = {
    ENABLE_I18N: process.env.REACT_APP_ENABLE_I18N === 'true',
    ENABLE_RTL: process.env.REACT_APP_ENABLE_RTL === 'true',
    ENABLE_UNIT_TOGGLE: process.env.REACT_APP_ENABLE_UNIT_TOGGLE === 'true',
} as const;

// Usage
if (FEATURE_FLAGS.ENABLE_I18N) {
    return <LanguageSwitcher />;
}
```

---

## 15. 🏗️ BUILD & DEPLOYMENT

### Build Commands

```json
// package.json scripts
{
  "start": "react-scripts start",         // Development server
  "build": "react-scripts build",         // Production build
  "test": "react-scripts test",           // Run tests
  "eject": "react-scripts eject"          // Eject from CRA (not recommended)
}
```

### Development Server

```bash
npm start
```

**Details:**
- **Port:** 3000 (default)
- **Hot Reload:** ✅ Enabled
- **URL:** http://localhost:3000
- **Proxy:** None configured (uses direct API calls to localhost:8000)

### Production Build

```bash
npm run build
```

**Output:**
- **Directory:** `build/`
- **Optimizations:**
  - ✅ Minification
  - ✅ Tree shaking
  - ✅ Code splitting
  - ✅ Source maps (optional)

**Build Artifacts:**
```
build/
├── static/
│   ├── js/
│   │   ├── main.[hash].js
│   │   └── [chunk].[hash].js
│   ├── css/
│   │   └── main.[hash].css
│   └── media/
│       └── [assets]
├── index.html
├── manifest.json
└── favicon.ico
```

### Docker Deployment

#### Development Dockerfile (`Dockerfile.dev`)
```dockerfile
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

#### Production Dockerfile (`Dockerfile.prod`)
```dockerfile
# Build stage
FROM node:18 as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage with nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Nginx Configuration (`nginx.conf`)
Serves the built React app and proxies API requests to backend.

### Deployment Process

**Docker Compose (from root):**
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up
```

**Manual Build:**
```bash
cd frontend
npm install
npm run build
# Serve build/ directory with nginx or any static server
```

### Environment-Specific Builds

**Create React App supports:**
- `.env` - Default
- `.env.local` - Local overrides (gitignored)
- `.env.development` - Development only
- `.env.production` - Production only

**Access in code:**
```typescript
// Only variables starting with REACT_APP_ are exposed
const apiUrl = process.env.REACT_APP_API_URL;
```

### Build Configuration

**Webpack:** Handled by CRA (not ejected)

**No custom build config** - Using defaults:
- ✅ Babel transpilation
- ✅ CSS/SCSS support
- ✅ Image optimization
- ✅ Font handling
- ✅ SVG import

---

## 16. 🎯 INTEGRATION CHECKLIST

### For Implementing Multilingual Support

- [ ] Install i18next libraries (`react-i18next`, `i18next`, `i18next-browser-languagedetector`)
- [ ] Create translation files (`src/locales/en.json`, `ru.json`, `he.json`)
- [ ] Initialize i18n (`src/i18n.ts`)
- [ ] Wrap app with i18n provider
- [ ] Replace all hardcoded text with `t()` function
- [ ] Create LanguageSwitcher component
- [ ] Fetch user's preferred_language from `/api/users/profile/preferences/`
- [ ] Set i18n language on login
- [ ] Update language in backend when user changes it
- [ ] Install Tailwind RTL plugin for Hebrew support
- [ ] Add RTL direction switching
- [ ] Test all pages in all 3 languages
- [ ] Test RTL layout for Hebrew

### For Implementing Unit System Toggle

- [ ] Create UnitToggle component
- [ ] Fetch user's unit_system from `/api/users/profile/preferences/`
- [ ] Store unit_system in context (AuthContext or new PreferencesContext)
- [ ] Create utility function for unit conversion
- [ ] Update all ingredient displays to show both units
- [ ] Add unit toggle to Navigation or Settings
- [ ] Persist unit_system to backend on change
- [ ] Apply unit conversion in recipe display
- [ ] Apply unit conversion in inventory display
- [ ] Apply unit conversion in nutrition tracking
- [ ] Test all conversions (metric ↔ imperial)

### For Displaying IML-Enriched Data

- [ ] Update RecipeCard to show nutrition label
- [ ] Create NutritionLabel component
- [ ] Display `nutrition_per_serving` prominently
- [ ] Show `nutrition_coverage` percentage
- [ ] Create SourceBadge component (IML/AI/Default)
- [ ] Display source badge with confidence score
- [ ] Show ingredient_key in ingredient details
- [ ] Display alternative units (metric & imperial)
- [ ] Show original_language indicator
- [ ] Implement language fallback (if translation missing, show original)

### For Integrating UserPreferences API

- [ ] Add getUserPreferences() to ApiService
- [ ] Add updateUserPreferences() to ApiService
- [ ] Fetch preferences on login (in AuthContext)
- [ ] Store preferences in context/state
- [ ] Update User interface to include preferences
- [ ] Use preferred_language throughout app
- [ ] Use unit_system throughout app
- [ ] Sync SettingsPage with preferences API
- [ ] Implement preference update handlers
- [ ] Add optimistic updates for better UX

### For Enhanced Recipe Display

- [ ] Check for title_translations and use user's language
- [ ] Check for description_translations and use user's language
- [ ] Check for steps_translations and use user's language
- [ ] Fallback to original if translation doesn't exist
- [ ] Show original_language badge if viewing translation
- [ ] Add "View in original language" button
- [ ] Display multilingual ingredient names if available
- [ ] Show ingredient match confidence

### Testing Checklist

- [ ] Test language switching (EN → RU → HE)
- [ ] Test RTL layout in Hebrew
- [ ] Test unit system toggle (metric ↔ imperial)
- [ ] Test recipe display in all languages
- [ ] Test unit conversions accuracy
- [ ] Test nutrition label display
- [ ] Test source badges (IML/AI/Default)
- [ ] Test preferences persistence across sessions
- [ ] Test missing translations fallback
- [ ] Test mobile responsiveness in all languages
- [ ] Test WebSocket real-time updates with new data
- [ ] Verify API calls include correct language/unit params

---

## 17. 📊 SUMMARY STATUS TABLE

| Feature | Frontend Status | Backend Status | Integration Priority |
|---------|----------------|----------------|---------------------|
| **i18n Library** | ❌ Not installed | ✅ Ready | 🔴 Critical |
| **Translation Files** | ❌ Don't exist | ✅ Backend provides | 🔴 Critical |
| **Language Switcher** | ⚠️ UI exists, no function | ✅ API ready | 🔴 Critical |
| **Unit System Toggle** | ❌ Not implemented | ✅ API ready | 🔴 Critical |
| **UserPreferences API** | ❌ Not integrated | ✅ Fully implemented | 🔴 Critical |
| **Multilingual Recipes** | ❌ Shows English only | ✅ Translations ready | 🔴 Critical |
| **RTL Support** | ❌ Not implemented | N/A | 🟠 High (for Hebrew) |
| **Nutrition Label** | ❌ Missing component | ✅ Data provided | 🟠 High |
| **Source Badges** | ❌ Not displayed | ✅ Data provided | 🟠 High |
| **Unit Alternatives** | ❌ Not shown | ✅ Data provided | 🟡 Medium |
| **Recipe Card Enhancement** | ⚠️ Partial | ✅ All data ready | 🟡 Medium |
| **Settings Page** | ⚠️ Partial | ✅ API ready | 🟡 Medium |

---

## 18. 🚀 RECOMMENDED IMPLEMENTATION ORDER

### Phase 1: UserPreferences Integration (Week 1)
1. Add getUserPreferences() to ApiService
2. Fetch preferences on login
3. Store in AuthContext (extend User interface)
4. Test preference retrieval

### Phase 2: i18n Foundation (Week 1-2)
1. Install i18next and dependencies
2. Create basic translation files (en.json, ru.json, he.json)
3. Set up i18n initialization
4. Translate Navigation component as proof of concept
5. Test language switching

### Phase 3: Language Switcher (Week 2)
1. Create LanguageSwitcher component
2. Add to Navigation
3. Connect to UserPreferences API
4. Sync user's preferred_language on login
5. Persist changes to backend

### Phase 4: Unit System Toggle (Week 2-3)
1. Create UnitToggle component
2. Add to Navigation or Settings
3. Create unit conversion utility
4. Connect to UserPreferences API
5. Test conversions

### Phase 5: Multilingual Recipe Display (Week 3)
1. Update RecipeCard to check title_translations
2. Use user's language for display
3. Implement fallback to original
4. Add original_language indicator
5. Test all translations

### Phase 6: RTL Support (Week 3-4)
1. Install tailwindcss-rtl
2. Update tailwind.config.js
3. Add RTL classes to components
4. Test Hebrew layout
5. Fix RTL-specific issues

### Phase 7: Nutrition & Source Badges (Week 4)
1. Create NutritionLabel component
2. Create SourceBadge component
3. Update RecipeCard to show both
4. Display ingredient alternatives
5. Test all data display

### Phase 8: Full Translation Rollout (Week 5+)
1. Translate all components systematically
2. Translate all pages
3. Test comprehensively
4. Fix edge cases
5. User acceptance testing

---

## 19. 💡 QUICK REFERENCE

### Key Files to Modify

| File | Purpose | Priority |
|------|---------|----------|
| `src/contexts/AuthContext.tsx` | Add user preferences | 🔴 Critical |
| `src/services/api.ts` | Add preferences endpoints | 🔴 Critical |
| `src/components/Navigation.tsx` | Add lang/unit switchers | 🔴 Critical |
| `src/components/RecipeCard.tsx` | Show multilingual & nutrition | 🟠 High |
| `src/i18n.ts` | Initialize i18n (NEW FILE) | 🔴 Critical |
| `src/locales/*.json` | Translation files (NEW FILES) | 🔴 Critical |
| `tailwind.config.js` | Add RTL plugin | 🟠 High |
| `.env` | API URL config (NEW FILE) | 🟡 Medium |

### Quick Code Snippets

**Fetch User Preferences:**
```typescript
// In AuthContext
const prefs = await api.get('/users/profile/preferences/');
setUser({ ...userData, preferred_language: prefs.preferred_language, unit_system: prefs.unit_system });
```

**Use Translation:**
```typescript
import { useTranslation } from 'react-i18next';
const { t } = useTranslation();
<button>{t('common.save')}</button>
```

**Show Multilingual Title:**
```typescript
const { i18n } = useTranslation();
const title = recipe.title_translations?.[i18n.language] || recipe.name;
```

**Convert Units:**
```typescript
const display = userUnitSystem === 'metric' 
    ? ingredient.alternatives.metric 
    : ingredient.alternatives.imperial;
```

---

## 20. 📞 HANDOFF NOTES

### Current State
- ✅ Solid foundation with TypeScript & Tailwind
- ✅ Authentication & API integration working well
- ✅ Most backend features have frontend counterparts
- ⚠️ **Zero i18n implementation** - biggest gap
- ⚠️ **No UserPreferences integration** - easy win
- ❌ **Missing unit system** - needs implementation

### Strengths
- Clean component structure
- Good TypeScript usage
- Consistent error handling patterns
- Real-time features working (WebSocket)
- Comprehensive API service class

### Weaknesses
- No i18n library (required for multilingual)
- Hardcoded API URLs (no .env)
- Custom routing instead of React Router (may limit future)
- No RTL support (needed for Hebrew)
- Zustand placeholder but not used

### Quick Wins
1. **Add .env file** - 15 minutes
2. **Install i18next** - 30 minutes
3. **Fetch UserPreferences** - 1 hour
4. **Add LanguageSwitcher** - 2 hours
5. **Show multilingual titles** - 2 hours

### Biggest Challenges
1. **Full translation coverage** - All text needs translation keys
2. **RTL layout** - Hebrew requires careful testing
3. **Unit conversions** - Must be accurate across all displays
4. **Migration without breaking** - Large user base requires careful rollout

### Recommended Approach
Start with **UserPreferences integration** → **i18n setup** → **Language switcher** → **Multilingual recipe display** → **RTL** → **Unit system** → **Full translation coverage**

---

**END OF HANDOFF DOCUMENTATION**

*Generated for AI assistant knowledge transfer - October 14, 2025*

