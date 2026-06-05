import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useCollaboration } from '../contexts/CollaborationContext';
import { Collaborator } from '../types';

interface CollaboratorManagerProps {
    listId?: string;
    canInvite?: boolean;
}

const CollaboratorManager: React.FC<CollaboratorManagerProps> = ({ listId, canInvite }) => {
    const { t } = useTranslation();
    const {
        collaborators,
        myCollaborationKey,
        addCollaborator,
        updatePermissions,
        loadMyCollaborationKey,
        generateNewCollaborationKey
    } = useCollaboration();

    const [showAddForm, setShowAddForm] = useState(false);
    const [friendEmail, setFriendEmail] = useState('');
    const [collaborationKey, setCollaborationKey] = useState('');
    const [canEdit, setCanEdit] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showMyKey, setShowMyKey] = useState(false);

    useEffect(() => {
        if (!myCollaborationKey) {
            loadMyCollaborationKey();
        }
    }, [myCollaborationKey, loadMyCollaborationKey]);

    const handleAddCollaborator = async (e: React.FormEvent) => {
        e.preventDefault();
        console.log(`🔥 handleAddCollaborator triggered: friendEmail="${friendEmail}", key="${collaborationKey}", listId="${listId}"`);

        if (isSubmitting) {
            console.warn('⚠️ handleAddCollaborator: Already submitting, ignoring duplicate submission');
            return;
        }

        if (!friendEmail.trim() || !collaborationKey.trim()) {
            console.warn('⚠️ handleAddCollaborator: Missing required fields');
            return;
        }

        setIsSubmitting(true);
        try {
            const success = await addCollaborator(friendEmail.trim(), collaborationKey.trim(), canEdit);

            if (success) {
                // Reset form
                setFriendEmail('');
                setCollaborationKey('');
                setCanEdit(true);
                setShowAddForm(false);
            }
        } catch (error) {
            console.error('Error adding collaborator:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handlePermissionChange = async (collaborator: Collaborator, permission: string, value: boolean) => {
        try {
            const permissions = {
                [permission]: value,
                // Keep other permissions unchanged
                can_edit: permission === 'can_edit' ? value : collaborator.can_edit,
                can_add_items: permission === 'can_add_items' ? value : collaborator.can_add_items,
                can_invite_others: permission === 'can_invite_others' ? value : collaborator.can_invite_others,
            };

            await updatePermissions(collaborator.id, permissions);
        } catch (error) {
            console.error('Error updating permissions:', error);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        // You could add a toast notification here
    };

    return (
        <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold">
                    {listId ? `👥 ${t('collaboration.titleWithCount', { count: collaborators.length })}` : `🤝 ${t('collaboration.collaboration')}`}
                </h3>
                {listId && canInvite && (
                    <button
                        onClick={() => {
                            console.log(`🔥 Add Friend button clicked: listId="${listId}", canInvite="${canInvite}", showAddForm="${showAddForm}"`);
                            setShowAddForm(!showAddForm);
                        }}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                    >
                        ➕ {t('collaboration.addFriend')}
                    </button>
                )}
            </div>

            {/* My Collaboration Key Section */}
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                <div className="flex justify-between items-center mb-3">
                    <h4 className="font-medium text-gray-700">🔑 {t('collaboration.myKey')}</h4>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setShowMyKey(!showMyKey)}
                            className="px-2 py-1 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-100 rounded transition"
                        >
                            {showMyKey ? `👁️ ${t('collaboration.hide')}` : `👁️ ${t('collaboration.show')}`}
                        </button>
                    </div>
                </div>

                {showMyKey && (
                    <div className="space-y-3">
                        {/* Key display - full width */}
                        <div className="w-full">
                            <code className="bg-white px-3 py-2 rounded border text-base font-mono tracking-wider block w-full break-all">
                                {myCollaborationKey || t('collaboration.loading')}
                            </code>
                        </div>

                        {/* Action buttons - centered below key */}
                        <div className="flex justify-center gap-3">
                            <button
                                onClick={() => myCollaborationKey && copyToClipboard(myCollaborationKey)}
                                className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
                                title={t('collaboration.copy')}
                            >
                                📋 {t('collaboration.copy')}
                            </button>
                            <button
                                onClick={generateNewCollaborationKey}
                                className="px-4 py-2 bg-orange-600 text-white text-sm rounded hover:bg-orange-700 transition"
                                title={t('collaboration.generateNew')}
                            >
                                🔄 {t('collaboration.generateNew')}
                            </button>
                        </div>

                        <p className="text-xs text-gray-600 text-center">
                            {t('collaboration.shareKeyDescription')}
                        </p>
                    </div>
                )}
            </div>

            {/* Add Collaborator Form - Only show when we have a list selected */}
            {listId && showAddForm && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                    <form onSubmit={handleAddCollaborator}>
                        <h4 className="font-medium mb-3">{t('collaboration.addNewCollaborator')}</h4>

                        <div className="space-y-3">
                            <div>
                                <label className="block text-sm font-medium mb-1">{t('collaboration.friendsEmail')}</label>
                                <input
                                    type="email"
                                    value={friendEmail}
                                    onChange={(e) => setFriendEmail(e.target.value)}
                                    placeholder={t('collaboration.enterFriendsEmail')}
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    required
                                    autoComplete="email"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">{t('collaboration.friendsKey')}</label>
                                <input
                                    type="text"
                                    value={collaborationKey}
                                    onChange={(e) => setCollaborationKey(e.target.value)}
                                    placeholder={t('collaboration.enter6DigitKey')}
                                    maxLength={6}
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 font-mono"
                                    required
                                />
                            </div>

                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    id="canEdit"
                                    checked={canEdit}
                                    onChange={(e) => setCanEdit(e.target.checked)}
                                    className="w-4 h-4 text-blue-600"
                                />
                                <label htmlFor="canEdit" className="ml-2 text-sm">
                                    {t('collaboration.allowEditing')}
                                </label>
                            </div>
                        </div>

                        <div className="flex gap-2 mt-4">
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                            >
                                {isSubmitting ? t('collaboration.adding') : t('collaboration.addCollaborator')}
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowAddForm(false)}
                                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                            >
                                {t('collaboration.cancel')}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Collaborators List - Only show when we have a list selected */}
            {listId && (
                <div className="space-y-3">
                    {collaborators.map((collaborator) => (
                        <div
                            key={collaborator.id}
                            className="p-3 border rounded-lg bg-white shadow-sm"
                        >
                            <div className="flex items-center gap-3">
                                <div
                                    className="w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold"
                                    style={{ backgroundColor: collaborator.color }}
                                >
                                    {collaborator.first_name.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">{collaborator.first_name}</span>
                                        <span className="text-gray-500">@{collaborator.username}</span>
                                        {collaborator.is_creator && (
                                            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                                                👑 {t('collaboration.creator')}
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-sm text-gray-500">
                                        {t('collaboration.joined')} {new Date(collaborator.joined_at).toLocaleDateString()}
                                    </div>
                                </div>
                            </div>

                            {/* Permission Controls (only for creator) */}
                            {!collaborator.is_creator && canInvite && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                    <div className="text-xs font-medium text-gray-500 mb-2">{t('collaboration.permissions')}</div>
                                    <div className="space-y-2">
                                        <label className="flex items-center text-sm cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={collaborator.can_edit}
                                                onChange={(e) => handlePermissionChange(collaborator, 'can_edit', e.target.checked)}
                                                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 mr-2"
                                            />
                                            <span className="text-gray-700">{t('collaboration.canEditItems')}</span>
                                        </label>
                                        <label className="flex items-center text-sm cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={collaborator.can_add_items}
                                                onChange={(e) => handlePermissionChange(collaborator, 'can_add_items', e.target.checked)}
                                                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 mr-2"
                                            />
                                            <span className="text-gray-700">{t('collaboration.canAddItems')}</span>
                                        </label>
                                        <label className="flex items-center text-sm cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={collaborator.can_invite_others}
                                                onChange={(e) => handlePermissionChange(collaborator, 'can_invite_others', e.target.checked)}
                                                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 mr-2"
                                            />
                                            <span className="text-gray-700">{t('collaboration.canInviteOthers')}</span>
                                        </label>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}

                    {collaborators.length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                            <p>{t('collaboration.noCollaborators')}</p>
                            <p className="text-sm">{t('collaboration.addFriendsToStart')}</p>
                        </div>
                    )}
                </div>
            )}

            {/* Show message when no list is selected */}
            {!listId && (
                <div className="text-center py-6 text-gray-500">
                    <p className="text-sm mb-2">{t('collaboration.selectListToManage')}</p>
                    <p className="text-xs text-gray-400">{t('collaboration.keyAlwaysAvailable')}</p>
                </div>
            )}
        </div>
    );
};

export default CollaboratorManager;

