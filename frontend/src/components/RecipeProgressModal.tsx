import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { userNotificationWS } from '../services/userWebSocket';

interface RecipeProgressModalProps {
    isOpen: boolean;
    onClose: () => void;
}

interface ProgressData {
    stage: string;
    percent: number;
    message: string;
    error?: boolean;
}

const RecipeProgressModal: React.FC<RecipeProgressModalProps> = ({ isOpen, onClose }) => {
    const { t } = useTranslation();
    const [progress, setProgress] = useState<ProgressData>({
        stage: 'searching',
        percent: 10,
        message: 'Starting...'
    });

    // CRITICAL FIX: Reset progress when modal opens
    useEffect(() => {
        if (isOpen) {
            console.log('[PROGRESS] Modal opened - RESETTING progress to initial state');
            setProgress({
                stage: 'searching',
                percent: 10,
                message: 'Starting...'
            });
        }
    }, [isOpen]);

    useEffect(() => {
        if (!isOpen) {
            console.log('[PROGRESS] Modal closed, not setting up listener');
            return;
        }

        console.log('[PROGRESS] Modal opened, registering listener for recipe_progress...');

        // Handler for recipe progress updates
        const handleProgress = (data: any) => {
            console.log('[PROGRESS] 📨 Recipe progress update received!');
            console.log('[PROGRESS] Full data:', data);
            console.log('[PROGRESS] Stage:', data.data?.stage);
            console.log('[PROGRESS] Percent:', data.data?.percent);
            console.log('[PROGRESS] Message:', data.data?.message);

            if (data.data) {
                setProgress(data.data);

                // Auto-close on complete
                if (data.data.stage === 'complete' && !data.data.error) {
                    console.log('[PROGRESS] ✅ Recipe complete! Auto-closing in 1.5s...');
                    setTimeout(() => {
                        console.log('[PROGRESS] Closing modal now');
                        onClose();
                    }, 1500);
                }

                if (data.data.error) {
                    console.error('[PROGRESS] ❌ Error in progress:', data.data.message);
                }
            } else {
                console.error('[PROGRESS] ❌ No data property in message!');
            }
        };

        // Register listener on the shared WebSocket service
        userNotificationWS.on('recipe_progress', handleProgress);
        console.log('[PROGRESS] ✅ Listener registered for recipe_progress on shared WebSocket');

        // Cleanup: Remove listener when modal closes or unmounts
        return () => {
            console.log('[PROGRESS] Cleanup: Removing recipe_progress listener');
            userNotificationWS.off('recipe_progress', handleProgress);
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const getStageIcon = () => {
        if (progress.error) return '❌';
        if (progress.stage === 'complete') return '✅';
        return '🔄';
    };

    const getProgressColor = () => {
        if (progress.error) return 'bg-red-500';
        if (progress.stage === 'complete') return 'bg-green-500';
        return 'bg-blue-500';
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                        {progress.error ? t('recipe.progress.error') :
                            progress.stage === 'complete' ? t('recipe.progress.complete') :
                                t('recipe.progress.generating')}
                    </h3>
                    <span className="text-2xl">{getStageIcon()}</span>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">{progress.message}</span>
                        <span className="text-sm font-semibold text-gray-900">{progress.percent}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                            className={`h-full ${getProgressColor()} transition-all duration-300 ease-out rounded-full`}
                            style={{ width: `${progress.percent}%` }}
                        />
                    </div>
                </div>

                {/* Message */}
                <p className="text-sm text-gray-500 text-center">
                    {progress.error ?
                        t('recipe.progress.error') :
                        progress.stage === 'complete' ?
                            t('recipe.progress.stages.complete') :
                            t('recipe.progress.stages.' + progress.stage, { defaultValue: progress.message })
                    }
                </p>

                {/* Close button (only show on error) */}
                {progress.error && (
                    <button
                        onClick={onClose}
                        className="mt-4 w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
                    >
                        Close
                    </button>
                )}
            </div>
        </div>
    );
};

export default RecipeProgressModal;
