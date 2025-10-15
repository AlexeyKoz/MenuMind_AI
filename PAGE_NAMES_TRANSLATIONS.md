# 🌍 Page Names & Tasks Translations

## ✅ Translation Keys Added

Added a new `pages` section to all three language files with translations for key pages and features.

---

## 📝 Translation Keys

### Usage in Code:
```typescript
import { useTranslation } from 'react-i18next';

const MyComponent = () => {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1>{t('pages.dashboard')}</h1>
      <h1>{t('pages.shoppingList')}</h1>
      <h1>{t('pages.inventory')}</h1>
      <h1>{t('pages.unitToggle')}</h1>
      <h1>{t('pages.nutritionTracker')}</h1>
    </div>
  );
};
```

---

## 🇬🇧 English (en.json)

```json
"pages": {
  "dashboard": "Dashboard",
  "shoppingList": "Shopping List",
  "inventory": "Inventory",
  "unitToggle": "Unit Toggle",
  "nutritionTracker": "Nutrition Tracker"
}
```

---

## 🇷🇺 Russian (ru.json)

```json
"pages": {
  "dashboard": "Панель управления",
  "shoppingList": "Список покупок",
  "inventory": "Запасы",
  "unitToggle": "Переключатель единиц",
  "nutritionTracker": "Трекер питания"
}
```

### Russian Translations Breakdown:
- **Dashboard** → **Панель управления** (Panel' upravleniya)
- **Shopping List** → **Список покупок** (Spisok pokupok)
- **Inventory** → **Запасы** (Zapasy)
- **Unit Toggle** → **Переключатель единиц** (Pereklyuchatel' yedinits)
- **Nutrition Tracker** → **Трекер питания** (Treker pitaniya)

---

## 🇮🇱 Hebrew (he.json)

```json
"pages": {
  "dashboard": "לוח בקרה",
  "shoppingList": "רשימת קניות",
  "inventory": "מלאי",
  "unitToggle": "החלפת יחידות",
  "nutritionTracker": "מעקב תזונה"
}
```

### Hebrew Translations Breakdown:
- **Dashboard** → **לוח בקרה** (Luach bakara)
- **Shopping List** → **רשימת קניות** (Reshimat kniyot)
- **Inventory** → **מלאי** (Milai)
- **Unit Toggle** → **החלפת יחידות** (Hachlafat yechidot)
- **Nutrition Tracker** → **מעקב תזונה** (Ma'akav tezuna)

---

## 📊 Translation Table

| Key | 🇬🇧 English | 🇷🇺 Russian | 🇮🇱 Hebrew |
|-----|-------------|-------------|-----------|
| `pages.dashboard` | Dashboard | Панель управления | לוח בקרה |
| `pages.shoppingList` | Shopping List | Список покупок | רשימת קניות |
| `pages.inventory` | Inventory | Запасы | מלאי |
| `pages.unitToggle` | Unit Toggle | Переключатель единиц | החלפת יחידות |
| `pages.nutritionTracker` | Nutrition Tracker | Трекер питания | מעקב תזונה |

---

## 🎯 Where to Use These Keys

### Example 1: Page Title
```typescript
// Dashboard.tsx
const Dashboard = () => {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1 className="text-3xl font-bold">{t('pages.dashboard')}</h1>
      {/* ... */}
    </div>
  );
};
```

### Example 2: Breadcrumbs
```typescript
// Breadcrumbs.tsx
const Breadcrumbs = ({ currentPage }) => {
  const { t } = useTranslation();
  
  return (
    <nav>
      <span>{t('nav.home')}</span> / 
      <span>{t(`pages.${currentPage}`)}</span>
    </nav>
  );
};
```

### Example 3: Task List
```typescript
// TaskList.tsx
const tasks = [
  { id: 1, name: t('pages.dashboard'), status: 'complete' },
  { id: 2, name: t('pages.shoppingList'), status: 'pending' },
  { id: 3, name: t('pages.inventory'), status: 'pending' },
  { id: 4, name: t('pages.unitToggle'), status: 'pending' },
  { id: 5, name: t('pages.nutritionTracker'), status: 'pending' }
];
```

### Example 4: Settings Navigation
```typescript
// SettingsNav.tsx
const settingsPages = [
  { icon: '📊', label: t('pages.dashboard'), route: '/dashboard' },
  { icon: '🛒', label: t('pages.shoppingList'), route: '/shopping' },
  { icon: '📦', label: t('pages.inventory'), route: '/inventory' },
  { icon: '📐', label: t('pages.unitToggle'), route: '/settings/units' },
  { icon: '🥗', label: t('pages.nutritionTracker'), route: '/nutrition' }
];
```

---

## ✅ Files Updated

1. ✅ `frontend/src/locales/en.json` - Added `pages` section
2. ✅ `frontend/src/locales/ru.json` - Added `pages` section with Russian translations
3. ✅ `frontend/src/locales/he.json` - Added `pages` section with Hebrew translations

---

## 🧪 How to Test

1. **In any component:**
   ```typescript
   import { useTranslation } from 'react-i18next';
   
   const TestComponent = () => {
     const { t } = useTranslation();
     
     return (
       <ul>
         <li>{t('pages.dashboard')}</li>
         <li>{t('pages.shoppingList')}</li>
         <li>{t('pages.inventory')}</li>
         <li>{t('pages.unitToggle')}</li>
         <li>{t('pages.nutritionTracker')}</li>
       </ul>
     );
   };
   ```

2. **Switch languages** using the LanguageSwitcher

3. **Verify translations** appear correctly in all three languages

---

## 📚 Related Keys

You can also still use the existing `nav` keys for navigation menus:
- `nav.shopping` → "Shopping" / "Покупки" / "קניות"
- `nav.dashboard` → "Dashboard" / "Панель управления" / "לוח בקרה"
- `nav.inventory` → "Inventory" / "Запасы" / "מלאי"
- `nav.nutrition` → "Nutrition" / "Питание" / "תזונה"

The new `pages` section provides more descriptive names for page titles and task lists.

---

**Translation completed successfully! 🎉**

All five page names are now available in English, Russian, and Hebrew.

