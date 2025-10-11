import React from 'react';

interface LeaveConfirmationModalProps {
    isOpen: boolean;
    listName: string;
    countdown: number;
    isLeaving: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

const LeaveConfirmationModal: React.FC<LeaveConfirmationModalProps> = ({
    isOpen,
    listName,
    countdown,
    isLeaving,
    onConfirm,
    onCancel
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div className="flex items-center mb-4">
                    <div className="bg-orange-100 rounded-full p-2 mr-3">
                        <span className="text-orange-600 text-xl">⚠️</span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900">
                        Remove Yourself from List?
                    </h3>
                </div>

                <div className="mb-6">
                    <p className="text-gray-600 mb-3">
                        You cannot delete <strong>"{listName}"</strong> because you are not the creator.
                    </p>
                    <p className="text-gray-700 font-medium">
                        Would you like to remove yourself from this list instead?
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                        • You will no longer see this list
                    </p>
                    <p className="text-sm text-gray-500">
                        • The creator will be notified that you left
                    </p>
                    <p className="text-sm text-gray-500">
                        • You can be re-invited later if needed
                    </p>
                </div>

                <div className="flex space-x-3">
                    <button
                        onClick={onCancel}
                        disabled={isLeaving}
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={isLeaving}
                        className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${isLeaving
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : countdown > 0
                                    ? 'bg-orange-500 text-white hover:bg-orange-600'
                                    : 'bg-red-600 text-white hover:bg-red-700'
                            }`}
                    >
                        {isLeaving
                            ? '🔄 Leaving...'
                            : countdown > 0
                                ? `🚪 Leave List (${countdown})`
                                : '🚪 Leave List Now'
                        }
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LeaveConfirmationModal;
