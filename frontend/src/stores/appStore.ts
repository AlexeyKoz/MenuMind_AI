// App Store - Disabled (zustand not installed)
// If you need state management, install zustand: npm install zustand

// Empty exports to prevent import errors
export const useAppStore = () => ({});
export const useSidebarState = () => ({ sidebarOpen: false, toggleSidebar: () => { } });
export const useThemeState = () => ({ theme: 'light', setTheme: () => { } });
export const useShoppingState = () => ({
    shoppingLists: [],
    currentShoppingList: null,
    setShoppingLists: () => { },
    setCurrentShoppingList: () => { }
});
export const useNutritionState = () => ({
    nutritionEntries: [],
    dailyGoals: { calories: 2000, protein: 150, carbs: 250, fat: 65 },
    addNutritionEntry: () => { },
    setDailyGoals: () => { }
});
