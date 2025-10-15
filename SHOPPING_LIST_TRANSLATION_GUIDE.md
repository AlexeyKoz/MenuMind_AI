# 🛒 Shopping List Translation Guide

## ✅ Translation Keys Added

Translation keys have been added to all three locale files:
- `frontend/src/locales/en.json`
- `frontend/src/locales/ru.json`
- `frontend/src/locales/he.json`

Under the new `shopping` section with 60+ keys covering all UI elements.

---

## 📝 Implementation Steps

### Step 1: Add useTranslation Hook ✅

At the top of `ShoppingList.tsx`, add the import and hook:

```typescript
import { useTranslation } from 'react-i18next';

const ShoppingList: React.FC = () => {
    const { t } = useTranslation();
    // ... rest of component
```

### Step 2: Key Areas to Translate

The `ShoppingList.tsx` component has these major sections that need translation:

#### 1. **Page Title & Header**
- Line ~1560: Page title
- Lines ~1580-1600: List sidebar section headers

#### 2. **List Management**
- "My Lists", "Shared with Me"
- "Create New List" button
- "New list name" input placeholder
- "Create", "Cancel" buttons

#### 3. **AI Input Section**
- AI placeholder text
- "AI Add", "Generating..." button states
- "AI Messages", "Generated Recipes" section headers
- "Clear" buttons and confirmation messages

#### 4. **Manual Item Input**
- "Add item manually..." placeholder
- "Select a list first..." placeholder
- "Add Item" button

#### 5. **Item List**
- "Added by", "Completed by" labels
- "New", "AI" badges
- "Remove item from list" title attribute
- Quantity type buttons: "Enable", "Weight", "Liquid"
- Counter titles: "Decrease/Increase quantity/weight/liquid"

#### 6. **Inventory Transfer Section**
- "Ready to Stock Up?" heading
- "Send X completed items to your inventory" text
- "Send to Inventory", "Processing..." button states

#### 7. **Store Order Section**
- "Order from Store (Mock)" heading
- "Order via Wolt" button
- "Check Shufersal Prices" button

#### 8. **Modals**
- Delete confirmation modal texts
- Leave confirmation modal texts
- Inventory review modal:
  - "Review AI Categorization" header
  - "Item Name", "Location", "Category", "Expires In" labels
  - "AI Confidence" label
  - "Add All to Inventory", "Cancel" buttons

#### 9. **Typing Indicators**
- "is typing...", "are typing..." dynamic text

#### 10. **Empty States**
- "Select or create a shopping list to get started"
- "No shopping lists yet"

---

## 🎯 Priority Translation Targets

### High Priority (Most Visible):
1. Page title: `<h1>` - Line ~1560
2. AI input placeholder - Line ~1730
3. Manual input placeholder - Line ~1907
4. Button texts: "Add Item", "AI Add", "Create", "Delete List", "Leave List"
5. Section headers: "My Lists", "Shared with Me", "AI Messages", "Generated Recipes"

### Medium Priority:
1. Modal titles and button texts
2. Tooltip titles (title attributes)
3. Confirmation messages (window.confirm)
4. Empty state messages

### Low Priority:
1. Console.log messages (can stay in English)
2. Developer-facing texts

---

## 📋 Translation Pattern Examples

### Simple Text Replacement:
```typescript
// Before:
<button>Add Item</button>

// After:
<button>{t('shopping.addItem')}</button>
```

### Placeholder Attributes:
```typescript
// Before:
placeholder="Add item manually..."

// After:
placeholder={t('shopping.addItemPlaceholder')}
```

### Title Attributes:
```typescript
// Before:
title="Remove item from list"

// After:
title={t('shopping.removeItem')}
```

### Conditional Text:
```typescript
// Before:
{loading ? 'Generating...' : 'AI Add'}

// After:
{loading ? t('shopping.generating') : t('shopping.aiAdd')}
```

### Dynamic Text with Variables:
```typescript
// Before:
<p>Send {items.filter(item => item.is_completed).length} completed items to your inventory</p>

// After:
<p>{t('shopping.sendCompletedItems', { count: items.filter(item => item.is_completed).length })}</p>
```

### Confirmation Dialogs:
```typescript
// Before:
if (window.confirm('Clear all AI messages?')) {

// After:
if (window.confirm(t('shopping.clearAllMessages'))) {
```

### Typing Indicator Logic:
```typescript
// Before:
{typingUsers.map(user => user.username).join(', ')}
{typingUsers.length === 1 ? ' is' : ' are'} typing...

// After:
{typingUsers.map(user => user.username).join(', ')}
{' '}{typingUsers.length === 1 ? t('shopping.isTyping') : t('shopping.areTyping')} {t('shopping.typing')}
```

---

## 🔍 Find & Replace Patterns

Use VS Code Find & Replace (Ctrl+H) with regex:

### 1. Simple Button Texts:
- Find: `>Add Item<`
- Replace: `>{t('shopping.addItem')}<`

### 2. Placeholders:
- Find: `placeholder="([^"]+)"`
- Check each match manually and replace with appropriate translation key

### 3. Title Attributes:
- Find: `title="([^"]+)"`
- Check each match manually and replace with appropriate translation key

---

## ✅ Verification Checklist

After translation, verify:

- [ ] All visible English text is replaced
- [ ] Placeholders are working in all 3 languages
- [ ] Button texts display correctly
- [ ] Confirmation dialogs show translated text
- [ ] Empty states are translated
- [ ] Modal titles and descriptions are translated
- [ ] Typing indicators work correctly
- [ ] Dynamic counts work (e.g., "{count} items")
- [ ] RTL layout works for Hebrew
- [ ] No console errors related to missing translation keys

---

## 🚀 Testing

1. **Switch languages** using the language switcher in navigation
2. **Test all UI elements** in each language (EN, RU, HE)
3. **Check RTL layout** for Hebrew (text alignment, icons, counters)
4. **Test dynamic texts** (typing indicators, counts, badges)
5. **Test modals** (delete, leave, inventory transfer)
6. **Test empty states** (no lists, no items)

---

## 📦 Complete Translation Keys Reference

All keys are under `shopping.*`:

| Key | English | Usage |
|-----|---------|-------|
| `title` | "Collaborative Shopping Lists" | Page title |
| `myLists` | "My Lists" | Section header |
| `sharedWithMe` | "Shared with Me" | Section header |
| `createNew` | "Create New List" | Button text |
| `newListName` | "New list name" | Input placeholder |
| `create` | "Create" | Button text |
| `cancel` | "Cancel" | Button text |
| `selectList` | "Select or create..." | Empty state |
| `addItem` | "Add Item" | Button text |
| `aiAdd` | "AI Add" | Button text |
| `generating` | "Generating..." | Loading state |
| ... and 50+ more keys |

See locale files for complete list.

---

**Due to the file's size (2341 lines), translation should be done systematically, section by section, with testing after each major section.**

