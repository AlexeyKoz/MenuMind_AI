import React from 'react';
import { Plus, Sparkles, Filter, Users } from 'lucide-react';
import { TouchTarget } from '../../../components/mobile/TouchTarget';
import { cn } from '../../../lib/utils';

interface BottomActionBarProps {
    onAddItem: () => void;
    onAIImport: () => void;
    onFilter: () => void;
    onCollaborators: () => void;
    collaboratorCount?: number;
    activeFilters?: number;
}

export const BottomActionBar: React.FC<BottomActionBarProps> = ({
    onAddItem,
    onAIImport,
    onFilter,
    onCollaborators,
    collaboratorCount = 0,
    activeFilters = 0
}) => {
    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t shadow-lg safe-area-inset-bottom">
            <div className="flex justify-around items-center py-2 px-4">
                {/* Add Item */}
                <ActionButton
                    onClick={onAddItem}
                    icon={Plus}
                    label="Add"
                    variant="primary"
                />

                {/* AI Import */}
                <ActionButton
                    onClick={onAIImport}
                    icon={Sparkles}
                    label="AI"
                    variant="secondary"
                    iconColor="text-purple-600"
                    bgColor="bg-purple-100"
                />

                {/* Filter */}
                <ActionButton
                    onClick={onFilter}
                    icon={Filter}
                    label="Filter"
                    variant="secondary"
                    badge={activeFilters > 0 ? activeFilters : undefined}
                />

                {/* Collaborators */}
                <ActionButton
                    onClick={onCollaborators}
                    icon={Users}
                    label="Share"
                    variant="secondary"
                    badge={collaboratorCount > 0 ? collaboratorCount : undefined}
                    iconColor="text-green-600"
                    bgColor="bg-green-100"
                />
            </div>
        </div>
    );
};

interface ActionButtonProps {
    onClick: () => void;
    icon: React.ElementType;
    label: string;
    variant?: 'primary' | 'secondary';
    badge?: number;
    iconColor?: string;
    bgColor?: string;
}

const ActionButton: React.FC<ActionButtonProps> = ({
    onClick,
    icon: Icon,
    label,
    variant = 'secondary',
    badge,
    iconColor = 'text-gray-700',
    bgColor = 'bg-gray-100'
}) => {
    return (
        <TouchTarget size={56} onClick={onClick} className="flex-col gap-1">
            <div className="relative">
                <div
                    className={cn(
                        'w-12 h-12 rounded-full flex items-center justify-center',
                        variant === 'primary'
                            ? 'bg-blue-600'
                            : bgColor
                    )}
                >
                    <Icon
                        className={cn(
                            'w-6 h-6',
                            variant === 'primary' ? 'text-white' : iconColor
                        )}
                    />
                </div>

                {badge !== undefined && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                        {badge}
                    </span>
                )}
            </div>

            <span className="text-xs font-medium text-gray-700">{label}</span>
        </TouchTarget>
    );
};

