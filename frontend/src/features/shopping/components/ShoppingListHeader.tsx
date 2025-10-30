import React from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import { TouchTarget } from '../../../components/mobile/TouchTarget';

interface ShoppingListHeaderProps {
    listName: string;
    completedCount: number;
    totalCount: number;
    showCompleted: boolean;
    onToggleCompleted: () => void;
}

export const ShoppingListHeader: React.FC<ShoppingListHeaderProps> = ({
    listName,
    completedCount,
    totalCount,
    showCompleted,
    onToggleCompleted
}) => {
    return (
        <div className="bg-white border-b sticky top-0 z-40">
            <div className="px-4 py-4">
                {/* Title and Progress */}
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">{listName}</h1>
                        <p className="text-sm text-gray-600 mt-1">
                            {completedCount} of {totalCount} completed
                        </p>
                    </div>

                    <TouchTarget size={44} onClick={onToggleCompleted}>
                        <div className="px-3 py-1.5 bg-gray-100 rounded-lg">
                            <span className="text-sm font-medium">
                                {showCompleted ? 'Hide' : 'Show'} Done
                            </span>
                        </div>
                    </TouchTarget>
                </div>

                {/* Progress Bar */}
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-blue-600 transition-all duration-300"
                        style={{ width: `${totalCount > 0 ? (completedCount / totalCount) * 100 : 0}%` }}
                    />
                </div>
            </div>
        </div>
    );
};

