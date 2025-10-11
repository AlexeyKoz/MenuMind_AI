import React, { useState, useEffect } from 'react';

interface DeleteConfirmationModalProps {
    isOpen: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    listName: string;
    countdown: number;
    isDeleting?: boolean;
}

const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({
    isOpen,
    onConfirm,
    onCancel,
    listName,
    countdown,
    isDeleting = false
}) => {
    if (!isOpen) return null;

    const getCountdownColor = (seconds: number) => {
        if (seconds > 3) return 'text-gray-600';
        if (seconds > 1) return 'text-orange-500';
        return 'text-red-500';
    };

    const getProgressPercentage = (seconds: number) => {
        return ((5 - seconds) / 5) * 100;
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
                {/* Header */}
                <div className="flex items-center justify-center mb-4">
                    <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                        <span className="text-2xl">🗑️</span>
                    </div>
                </div>

                {/* Content */}
                <div className="text-center mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        Delete Shopping List
                    </h3>
                    <p className="text-gray-600 mb-4">
                        Are you sure you want to delete <strong>"{listName}"</strong>?
                    </p>
                    <p className="text-sm text-gray-500">
                        The list will be moved to the Archive where you can restore it within 60 days.
                    </p>
                </div>

                {/* Countdown Display */}
                <div className="mb-6">
                    <div className="text-center mb-3">
                        <div className={`text-3xl font-bold ${getCountdownColor(countdown)}`}>
                            {countdown}
                        </div>
                        <div className="text-sm text-gray-500">
                            {countdown > 0 ? `Deleting in ${countdown} second${countdown !== 1 ? 's' : ''}` : 'Deleting...'}
                        </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className={`h-2 rounded-full transition-all duration-1000 ease-linear ${countdown > 3 ? 'bg-gray-400' : countdown > 1 ? 'bg-orange-400' : 'bg-red-500'
                                }`}
                            style={{ width: `${getProgressPercentage(countdown)}%` }}
                        />
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                    <button
                        onClick={onCancel}
                        disabled={isDeleting}
                        className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${isDeleting
                            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        ↩️ Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={isDeleting}
                        className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${isDeleting
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : countdown > 0
                                ? 'bg-orange-500 text-white hover:bg-orange-600'
                                : 'bg-red-600 text-white hover:bg-red-700'
                            }`}
                    >
                        {isDeleting ? '🔄 Deleting...' : countdown > 0 ? `🗑️ Delete (${countdown})` : '🗑️ Delete Now'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DeleteConfirmationModal;
