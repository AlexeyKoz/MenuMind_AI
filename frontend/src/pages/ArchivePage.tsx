import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import { toast } from 'react-hot-toast';

interface ArchivedList {
    id: string;
    name: string;
    deleted_at: string;
    permanently_deleted_at?: string | null;
    items_count: number;
    creator: {
        username: string;
        first_name: string;
    };
    can_restore: boolean;
    is_permanently_deleted: boolean;
    days_until_auto_delete: number;
}

interface ArchivedRecipe {
    id: string;
    name: string;
    description: string;
    cuisine: string;
    difficulty: string;
    total_time_minutes: number;
    servings: number;
    archived_at: string;
    times_cooked: number;
}

const ArchivePage: React.FC = () => {
    const { t } = useTranslation();
    const { token, logout } = useAuth();
    const [activeTab, setActiveTab] = useState<'lists' | 'recipes'>('lists');
    const [archivedLists, setArchivedLists] = useState<ArchivedList[]>([]);
    const [archivedRecipes, setArchivedRecipes] = useState<ArchivedRecipe[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
    const [selectedRecipes, setSelectedRecipes] = useState<Set<string>>(new Set());

    // Create API service with useMemo to prevent recreation on every render
    const api = useMemo(() => new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        alert(t('archive.sessionExpired'));
        logout();
    }), [token, logout, t]);

    const loadArchivedLists = async () => {
        try {
            setLoading(true);
            const response = await api.getArchivedLists();
            setArchivedLists(response.results || response);
        } catch (error) {
            console.error('Failed to load archived lists:', error);
            toast.error(t('archive.failedToLoadArchivedLists'));
        } finally {
            setLoading(false);
        }
    };

    const loadArchivedRecipes = async () => {
        try {
            setLoading(true);
            const response = await api.getArchivedRecipes();
            setArchivedRecipes(response.recipes || []);
        } catch (error) {
            console.error('Failed to load archived recipes:', error);
            toast.error(t('archive.failedToLoadArchivedRecipes'));
        } finally {
            setLoading(false);
        }
    };

    // Load both tabs on mount to show correct counts
    useEffect(() => {
        loadArchivedLists();
        loadArchivedRecipes();
    }, []);

    // Refresh when switching tabs
    useEffect(() => {
        if (activeTab === 'lists') {
            loadArchivedLists();
        } else {
            loadArchivedRecipes();
        }
    }, [activeTab]);

    // Refresh archive when page becomes visible
    useEffect(() => {
        const handleVisibilityChange = async () => {
            if (!document.hidden) {
                console.log('👀 Archive page became visible, refreshing...');
                await loadArchivedLists();
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, []);

    // Listen for list deletion events to refresh archive
    useEffect(() => {
        const handleListsChanged = async (event: any) => {
            const { type } = event.detail;
            console.log('🔔 Archive received listsChanged event:', type);

            if (type === 'list_deleted' || type === 'list_permanently_deleted' || type === 'ownership_transferred') {
                // Refresh archive when lists are deleted, permanently deleted, or ownership is transferred
                console.log('📋 Refreshing archive due to list changes');
                await loadArchivedLists();
            }
        };

        window.addEventListener('listsChanged', handleListsChanged);

        return () => {
            window.removeEventListener('listsChanged', handleListsChanged);
        };
    }, []);

    const handleRestore = async (listId: string) => {
        try {
            await api.restoreList(listId);
            toast.success(t('archive.listRestored'));
            await loadArchivedLists();
        } catch (error) {
            console.error('Failed to restore list:', error);
            toast.error(t('archive.failedToRestoreList'));
        }
    };


    const handlePermanentDelete = async (listId: string) => {
        if (!window.confirm(t('archive.confirmDeleteList'))) {
            return;
        }

        try {
            const response = await api.permanentDeleteList(listId);

            // Remove from selection state if it was selected
            if (selectedItems.has(listId)) {
                const newSelection = new Set(selectedItems);
                newSelection.delete(listId);
                setSelectedItems(newSelection);
            }

            // Show appropriate success message based on action
            if (response.action === 'permanent_delete') {
                toast.success(t('archive.listPermanentlyDeleted'));
            } else if (response.action === 'removed_from_view') {
                toast.success(t('archive.listRemovedFromArchive'));
            } else {
                toast.success(response.message || t('archive.listRemoved'));
            }

            await loadArchivedLists();
        } catch (error: any) {
            console.error('Failed to delete/remove list:', error);

            // Show specific error message
            let errorMessage = t('archive.failedToRemoveList');
            if (error.message) {
                if (error.message.includes('not found')) {
                    errorMessage = t('archive.listNotFound');
                } else if (error.message.includes('permission')) {
                    errorMessage = t('archive.noPermission');
                } else {
                    errorMessage = error.message;
                }
            }

            toast.error(errorMessage);
        }
    };

    const handleBulkPermanentDelete = async () => {
        if (selectedItems.size === 0) {
            toast.error(t('archive.pleaseSelectItems'));
            return;
        }

        if (!window.confirm(t('archive.confirmBulkDeleteLists', { count: selectedItems.size }))) {
            return;
        }

        const results = {
            successful: 0,
            failed: 0,
            errors: [] as string[]
        };

        // Process deletions individually to handle failures gracefully
        for (const listId of Array.from(selectedItems)) {
            try {
                const response = await api.permanentDeleteList(listId);
                results.successful++;
            } catch (error: any) {
                results.failed++;

                // Extract meaningful error message
                let errorMessage = 'Unknown error';
                if (error.message) {
                    if (error.message.includes('not found')) {
                        errorMessage = t('archive.listNotFound');
                    } else if (error.message.includes('permission')) {
                        errorMessage = t('archive.noPermission');
                    } else {
                        errorMessage = error.message;
                    }
                }

                results.errors.push(errorMessage);
                console.error(`Failed to delete list ${listId}:`, error);
            }
        }

        // Clear selections and reload
        setSelectedItems(new Set());
        await loadArchivedLists();

        // Show appropriate feedback based on results
        if (results.successful > 0 && results.failed === 0) {
            toast.success(t('archive.listsRemovedFromArchive', { count: results.successful }));
        } else if (results.successful > 0 && results.failed > 0) {
            toast.success(t('archive.listsRemovedSuccessfully', { count: results.successful }));
            toast.error(t('archive.listsCouldNotBeRemoved', { count: results.failed }));
        } else if (results.failed > 0) {
            toast.error(t('archive.failedToRemoveLists', { count: results.failed }));

            // Show specific errors if there are permission issues
            const permissionErrors = results.errors.filter(err => err.includes('permission')).length;
            const notFoundErrors = results.errors.filter(err => err.includes('not found')).length;

            if (permissionErrors > 0) {
                toast.error(t('archive.listsCouldNotBeRemovedNoAccess', { count: permissionErrors }));
            }
            if (notFoundErrors > 0) {
                toast.error(t('archive.listsAlreadyDeleted', { count: notFoundErrors }));
            }
        }
    };

    // Recipe Handlers
    const handleRestoreRecipe = async (recipeId: string) => {
        try {
            await api.restoreRecipe(recipeId);
            toast.success(t('archive.recipeRestored'));
            await loadArchivedRecipes();
        } catch (error) {
            console.error('Failed to restore recipe:', error);
            toast.error(t('archive.failedToRestoreRecipe'));
        }
    };

    const handlePermanentDeleteRecipe = async (recipeId: string) => {
        if (!window.confirm(t('archive.confirmDeleteRecipe'))) {
            return;
        }

        try {
            await api.permanentlyDeleteRecipe(recipeId);

            // Remove from selection state if it was selected
            if (selectedRecipes.has(recipeId)) {
                const newSelection = new Set(selectedRecipes);
                newSelection.delete(recipeId);
                setSelectedRecipes(newSelection);
            }

            toast.success(t('archive.recipePermanentlyDeleted'));
            await loadArchivedRecipes();
        } catch (error: any) {
            console.error('Failed to delete recipe:', error);
            toast.error(error.message || t('archive.failedToDeleteRecipe'));
        }
    };

    const handleSelectAll = () => {
        if (selectedItems.size === archivedLists.length) {
            setSelectedItems(new Set());
        } else {
            setSelectedItems(new Set(archivedLists.map(list => list.id)));
        }
    };

    const toggleSelection = (listId: string) => {
        const newSelection = new Set(selectedItems);
        if (newSelection.has(listId)) {
            newSelection.delete(listId);
        } else {
            newSelection.add(listId);
        }
        setSelectedItems(newSelection);
    };

    const handleSelectAllRecipes = () => {
        if (selectedRecipes.size === archivedRecipes.length) {
            setSelectedRecipes(new Set());
        } else {
            setSelectedRecipes(new Set(archivedRecipes.map(recipe => recipe.id)));
        }
    };

    const toggleRecipeSelection = (recipeId: string) => {
        const newSelection = new Set(selectedRecipes);
        if (newSelection.has(recipeId)) {
            newSelection.delete(recipeId);
        } else {
            newSelection.add(recipeId);
        }
        setSelectedRecipes(newSelection);
    };

    const handleBulkDeleteRecipes = async () => {
        if (selectedRecipes.size === 0) {
            toast.error(t('archive.pleaseSelectRecipes'));
            return;
        }

        const plural = selectedRecipes.size > 1 ? 's' : '';
        if (!window.confirm(t('archive.confirmBulkDeleteRecipes', { count: selectedRecipes.size, plural }))) {
            return;
        }

        const results = {
            successful: 0,
            failed: 0
        };

        // Process deletions individually to handle failures gracefully
        for (const recipeId of Array.from(selectedRecipes)) {
            try {
                await api.permanentlyDeleteRecipe(recipeId);
                results.successful++;
            } catch (error: any) {
                results.failed++;
                console.error(`Failed to delete recipe ${recipeId}:`, error);
            }
        }

        // Clear selections and reload
        setSelectedRecipes(new Set());
        await loadArchivedRecipes();

        // Show appropriate feedback
        const successPlural = results.successful > 1 ? 's' : '';
        const failedPlural = results.failed > 1 ? 's' : '';

        if (results.successful > 0 && results.failed === 0) {
            toast.success(t('archive.recipesPermanentlyDeleted', { count: results.successful, plural: successPlural }));
        } else if (results.successful > 0 && results.failed > 0) {
            toast.success(t('archive.recipesDeleted', { count: results.successful, plural: successPlural }));
            toast.error(t('archive.recipesCouldNotBeDeleted', { count: results.failed, plural: failedPlural }));
        } else if (results.failed > 0) {
            toast.error(t('archive.failedToDeleteRecipes', { count: results.failed, plural: failedPlural }));
        }
    };

    const getTimeUntilAutoDelete = (deletedAt: string) => {
        const deletedDate = new Date(deletedAt);
        const autoDeleteDate = new Date(deletedDate.getTime() + (60 * 24 * 60 * 60 * 1000)); // 60 days
        const now = new Date();
        const daysLeft = Math.ceil((autoDeleteDate.getTime() - now.getTime()) / (24 * 60 * 60 * 1000));

        if (daysLeft <= 0) {
            return t('archive.scheduledForDeletion');
        }
        return t(daysLeft === 1 ? 'archive.autoDeleteIn_one' : 'archive.autoDeleteIn', { days: daysLeft });
    };

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-6xl mx-auto px-4">
                {/* Header */}
                <div className="bg-white rounded-2xl shadow-sm ring-1 ring-gray-100 p-4 sm:p-6 mb-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                                🗃️ {t('archive.title')}
                            </h1>
                            <p className="text-gray-600 mt-1">
                                {activeTab === 'lists'
                                    ? t('archive.listsDescription')
                                    : t('archive.recipesDescription')}
                            </p>
                        </div>
                        <div className="flex gap-2">
                            {activeTab === 'lists' && selectedItems.size > 0 && (
                                <button
                                    onClick={handleBulkPermanentDelete}
                                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                                >
                                    🗑️ {t('archive.deleteSelected', { count: selectedItems.size })}
                                </button>
                            )}
                            {activeTab === 'recipes' && selectedRecipes.size > 0 && (
                                <button
                                    onClick={handleBulkDeleteRecipes}
                                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                                >
                                    🗑️ {t('archive.deleteSelected', { count: selectedRecipes.size })}
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-2 border-b">
                        <button
                            onClick={() => setActiveTab('lists')}
                            className={`px-4 py-2 font-medium transition-colors ${activeTab === 'lists'
                                ? 'text-blue-600 border-b-2 border-blue-600'
                                : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            🛒 {t('archive.shoppingLists')} ({archivedLists.length})
                        </button>
                        <button
                            onClick={() => setActiveTab('recipes')}
                            className={`px-4 py-2 font-medium transition-colors ${activeTab === 'recipes'
                                ? 'text-blue-600 border-b-2 border-blue-600'
                                : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            📖 {t('archive.recipes')} ({archivedRecipes.length})
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="bg-white rounded-2xl shadow-sm ring-1 ring-gray-100">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            <span className="ml-2 text-gray-600">{t('archive.loading')} {activeTab}...</span>
                        </div>
                    ) : activeTab === 'lists' ? (
                        // Shopping Lists Tab
                        archivedLists.length === 0 ? (
                            <div className="text-center py-12">
                                <div className="text-6xl mb-4">🎉</div>
                                <h3 className="text-lg font-medium text-gray-900 mb-2">{t('archive.noDeletedLists')}</h3>
                                <p className="text-gray-600">{t('archive.noDeletedListsDesc')}</p>
                            </div>
                        ) : (
                            <div className="p-6">
                                {/* Bulk Actions */}
                                <div className="flex items-center justify-between mb-4 pb-4 border-b">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={selectedItems.size === archivedLists.length && archivedLists.length > 0}
                                            onChange={handleSelectAll}
                                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                                        />
                                        <span className="text-sm text-gray-700">
                                            {t('archive.selectAll')} ({archivedLists.length} {t('archive.items')})
                                        </span>
                                    </label>

                                    <div className="text-sm text-gray-500">
                                        {selectedItems.size > 0 && `${selectedItems.size} ${t('archive.selected')}`}
                                    </div>
                                </div>

                                {/* Lists */}
                                <div className="space-y-3">
                                    {archivedLists.map((list) => (
                                        <div
                                            key={list.id}
                                            className={`p-4 border rounded-lg transition-colors ${selectedItems.has(list.id)
                                                ? 'border-blue-300 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                                }`}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedItems.has(list.id)}
                                                        onChange={() => toggleSelection(list.id)}
                                                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                                                    />

                                                    <div>
                                                        <h3 className="font-medium text-gray-900">{list.name}</h3>
                                                        <div className="text-sm text-gray-500 flex items-center gap-4">
                                                            <span>{t('archive.createdBy')} {list.creator.first_name} (@{list.creator.username})</span>
                                                            <span>•</span>
                                                            <span>{list.items_count} {t('archive.items')}</span>
                                                            <span>•</span>
                                                            <span>{t('archive.deleted')} {new Date(list.deleted_at).toLocaleDateString()}</span>
                                                        </div>
                                                        <div className="text-xs text-orange-600 mt-1">
                                                            {getTimeUntilAutoDelete(list.deleted_at)}
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-2">
                                                    {/* Show different buttons based on list state */}
                                                    {list.can_restore ? (
                                                        // List is only archived, not permanently deleted - show restore
                                                        <button
                                                            onClick={() => handleRestore(list.id)}
                                                            className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
                                                        >
                                                            ↩️ {t('archive.restore')}
                                                        </button>
                                                    ) : list.is_permanently_deleted ? (
                                                        // List is permanently deleted - no action available
                                                        <span className="px-3 py-1 text-sm bg-gray-100 text-gray-500 rounded-md">
                                                            {t('archive.permanentlyDeleted')}
                                                        </span>
                                                    ) : (
                                                        // Fallback for other cases
                                                        <span className="px-3 py-1 text-sm bg-gray-100 text-gray-500 rounded-md">
                                                            {t('archive.noActionsAvailable')}
                                                        </span>
                                                    )}

                                                    {/* Delete button - show different text based on state */}
                                                    {!list.is_permanently_deleted && (
                                                        <button
                                                            onClick={() => handlePermanentDelete(list.id)}
                                                            className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
                                                        >
                                                            🗑️ {t('archive.deletePerm')}
                                                        </button>
                                                    )}

                                                    {/* Always show remove from view for participants */}
                                                    {list.is_permanently_deleted && (
                                                        <button
                                                            onClick={() => handlePermanentDelete(list.id)}
                                                            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                                                        >
                                                            🚫 {t('archive.removeFromView')}
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )
                    ) : (
                        // Recipes Tab
                        archivedRecipes.length === 0 ? (
                            <div className="text-center py-12">
                                <div className="text-6xl mb-4">📖</div>
                                <h3 className="text-lg font-medium text-gray-900 mb-2">{t('archive.noArchivedRecipes')}</h3>
                                <p className="text-gray-600">{t('archive.noArchivedRecipesDesc')}</p>
                            </div>
                        ) : (
                            <div className="p-6">
                                {/* Bulk Actions */}
                                <div className="flex items-center justify-between mb-4 pb-4 border-b">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={selectedRecipes.size === archivedRecipes.length && archivedRecipes.length > 0}
                                            onChange={handleSelectAllRecipes}
                                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                                        />
                                        <span className="text-sm text-gray-700">
                                            {t('archive.selectAll')} ({archivedRecipes.length} {t('archive.recipes')})
                                        </span>
                                    </label>

                                    <div className="text-sm text-gray-500">
                                        {selectedRecipes.size > 0 && `${selectedRecipes.size} ${t('archive.selected')}`}
                                    </div>
                                </div>

                                {/* Recipes */}
                                <div className="space-y-3">
                                    {archivedRecipes.map((item) => (
                                        <div
                                            key={item.id}
                                            className={`p-4 border rounded-lg transition-colors ${selectedRecipes.has(item.id)
                                                ? 'border-blue-300 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                                }`}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedRecipes.has(item.id)}
                                                        onChange={() => toggleRecipeSelection(item.id)}
                                                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                                                    />

                                                    <div className="flex-1">
                                                        <h3 className="font-medium text-gray-900 text-lg">{item.name}</h3>
                                                        <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                                                        <div className="text-sm text-gray-500 flex items-center gap-4 mt-2">
                                                            <span>🍳 {item.cuisine}</span>
                                                            <span>•</span>
                                                            <span>⏱️ {item.total_time_minutes} {t('archive.min')}</span>
                                                            <span>•</span>
                                                            <span>👥 {item.servings} {t('archive.servings')}</span>
                                                            <span>•</span>
                                                            <span>📊 {item.difficulty}</span>
                                                        </div>
                                                        <div className="text-xs text-gray-500 mt-2">
                                                            {t('archive.archived')} {new Date(item.archived_at).toLocaleDateString()} • {t('archive.cooked')} {item.times_cooked} {t('archive.times')}
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => handleRestoreRecipe(item.id)}
                                                        className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
                                                    >
                                                        ↩️ {t('archive.restore')}
                                                    </button>
                                                    <button
                                                        onClick={() => handlePermanentDeleteRecipe(item.id)}
                                                        className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
                                                    >
                                                        🗑️ {t('archive.deletePermanently')}
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )
                    )}
                </div>

                {/* Info Box */}
                <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <div className="text-blue-600 text-xl">ℹ️</div>
                        <div>
                            <h4 className="font-medium text-blue-900 mb-1">{t('archive.archivePolicy')}</h4>
                            <ul className="text-sm text-blue-800 space-y-1">
                                {activeTab === 'lists' ? (
                                    <>
                                        <li>• {t('archive.policyLists1')}</li>
                                        <li>• {t('archive.policyLists2')}</li>
                                        <li>• {t('archive.policyLists3')}</li>
                                        <li>• {t('archive.policyLists4')}</li>
                                    </>
                                ) : (
                                    <>
                                        <li>• {t('archive.policyRecipes1')}</li>
                                        <li>• {t('archive.policyRecipes2')}</li>
                                        <li>• {t('archive.policyRecipes3')}</li>
                                        <li>• {t('archive.policyRecipes4')}</li>
                                    </>
                                )}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ArchivePage;
