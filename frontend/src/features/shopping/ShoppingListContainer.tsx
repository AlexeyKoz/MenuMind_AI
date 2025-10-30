import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { ShoppingListHeader } from './components/ShoppingListHeader';
import { CategorySection } from './components/CategorySection';
import { BottomActionBar } from './components/BottomActionBar';
import { QuickAddDrawer } from './components/QuickAddDrawer';
import { useShoppingItems } from './hooks/useShoppingItems';
import { useNetworkStatus } from './hooks/useNetworkStatus';
import { syncQueueService } from './services/syncQueue';

const CATEGORY_ORDER = [
  { id: 'produce', icon: '🥬', label: 'Produce' },
  { id: 'dairy', icon: '🥛', label: 'Dairy' },
  { id: 'meat', icon: '🥩', label: 'Meat' },
  { id: 'bakery', icon: '🍞', label: 'Bakery' },
  { id: 'frozen', icon: '🧊', label: 'Frozen' },
  { id: 'pantry', icon: '🥫', label: 'Pantry' },
  { id: 'beverages', icon: '🥤', label: 'Beverages' },
  { id: 'other', icon: '📦', label: 'Other' }
];

export const ShoppingListContainer: React.FC = () => {
  const { listId } = useParams<{ listId: string }>();
  const { isOnline } = useNetworkStatus();
  
  const {
    items,
    loading,
    toggleComplete,
    updateQuantity,
    addItem,
    deleteItem
  } = useShoppingItems(listId || 'default');

  const [isQuickAddOpen, setIsQuickAddOpen] = useState(false);
  const [showCompleted, setShowCompleted] = useState(true);

  // Start sync queue service
  useEffect(() => {
    syncQueueService.start();
    return () => syncQueueService.stop();
  }, []);

  // Group items by category
  const groupedItems = useMemo(() => {
    const filteredItems = showCompleted 
      ? items 
      : items.filter(item => !item.is_completed);

    const groups = new Map<string, typeof items>();
    
    filteredItems.forEach(item => {
      const category = item.category || 'other';
      if (!groups.has(category)) {
        groups.set(category, []);
      }
      groups.get(category)!.push(item);
    });

    return CATEGORY_ORDER
      .map(cat => ({
        ...cat,
        items: groups.get(cat.id) || []
      }))
      .filter(group => group.items.length > 0);
  }, [items, showCompleted]);

  const handleAddItem = async (itemData: {
    name: string;
    quantity: number;
    category: string;
  }) => {
    await addItem(itemData);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-gray-600">Loading shopping list...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* Connection Status */}
      <div className={`fixed top-0 left-0 right-0 z-50 transition-transform ${
        isOnline ? '-translate-y-full' : 'translate-y-0'
      }`}>
        <div className="bg-yellow-500 text-white text-center py-2 text-sm font-medium">
          ⚠️ You are offline. Changes will sync when connection is restored.
        </div>
      </div>

      {/* Header */}
      <ShoppingListHeader
        listName="My Shopping List"
        completedCount={items.filter(i => i.is_completed).length}
        totalCount={items.length}
        showCompleted={showCompleted}
        onToggleCompleted={() => setShowCompleted(!showCompleted)}
      />

      {/* Shopping List */}
      <div className="px-4 pt-4">
        {groupedItems.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">Your shopping list is empty</p>
            <button
              onClick={() => setIsQuickAddOpen(true)}
              className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium"
            >
              Add Your First Item
            </button>
          </div>
        ) : (
          groupedItems.map(category => (
            <CategorySection
              key={category.id}
              category={category}
              onToggleItem={toggleComplete}
              onUpdateQuantity={updateQuantity}
              onDeleteItem={deleteItem}
            />
          ))
        )}
      </div>

      {/* Bottom Action Bar */}
      <BottomActionBar
        onAddItem={() => setIsQuickAddOpen(true)}
        onAIImport={() => {/* TODO: Implement AI import */}}
        onFilter={() => {/* TODO: Implement filter */}}
        onCollaborators={() => {/* TODO: Implement collaborators */}}
        collaboratorCount={0}
        activeFilters={0}
      />

      {/* Quick Add Drawer */}
      <QuickAddDrawer
        isOpen={isQuickAddOpen}
        onClose={() => setIsQuickAddOpen(false)}
        onAddItem={handleAddItem}
        recentItems={[]}
      />
    </div>
  );
};

