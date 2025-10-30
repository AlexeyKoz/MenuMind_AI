import React, { useEffect, useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { X, ChevronRight, Sparkles } from 'lucide-react';
import { useUserGuide } from '../contexts/UserGuideContext';

interface Position {
    top?: number;
    left?: number;
    right?: number;
    bottom?: number;
}

export const GuideTooltip: React.FC = () => {
    const { t } = useTranslation();
    const { currentStep, nextStep, skipGuide, isGuideActive } = useUserGuide();
    const [position, setPosition] = useState<Position>({});
    const [isVisible, setIsVisible] = useState(false);
    const tooltipRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!currentStep || !isGuideActive) {
            setIsVisible(false);
            return;
        }

        // Show with slight delay for better UX
        const showTimer = setTimeout(() => {
            calculatePosition();
            setIsVisible(true);
        }, 300);

        return () => clearTimeout(showTimer);
    }, [currentStep, isGuideActive]);

    useEffect(() => {
        // Recalculate position on window resize
        const handleResize = () => {
            if (currentStep && isGuideActive) {
                calculatePosition();
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [currentStep, isGuideActive]);

    const calculatePosition = () => {
        if (!currentStep) return;

        const isMobile = window.innerWidth < 768;
        const tooltipWidth = isMobile ? Math.min(320, window.innerWidth - 32) : 400;
        const tooltipHeight = isMobile ? 180 : 200;
        const gap = isMobile ? 8 : 16;

        // Center position (no target element)
        if (currentStep.position === 'center' || !currentStep.elementId) {
            setPosition({
                top: window.innerHeight / 2 - (tooltipHeight / 2),
                left: window.innerWidth / 2
            });
            return;
        }

        // Target element position
        const element = document.getElementById(currentStep.elementId);
        if (!element) {
            console.warn(`Element with id "${currentStep.elementId}" not found`);
            // Fallback to center
            setPosition({
                top: window.innerHeight / 2 - (tooltipHeight / 2),
                left: window.innerWidth / 2
            });
            return;
        }

        const rect = element.getBoundingClientRect();
        let newPosition: Position = {};

        // On mobile, prefer bottom positioning for better visibility
        if (isMobile) {
            // Check if there's room below
            if (rect.bottom + tooltipHeight + gap < window.innerHeight) {
                newPosition = {
                    top: rect.bottom + gap,
                    left: 16 // Fixed left margin on mobile
                };
            } else if (rect.top - tooltipHeight - gap > 0) {
                // Try above
                newPosition = {
                    bottom: window.innerHeight - rect.top + gap,
                    left: 16
                };
            } else {
                // Fallback to center
                newPosition = {
                    top: window.innerHeight / 2 - (tooltipHeight / 2),
                    left: 16
                };
            }
        } else {
            // Desktop positioning
            switch (currentStep.position) {
                case 'top':
                    newPosition = {
                        bottom: window.innerHeight - rect.top + gap,
                        left: Math.max(16, Math.min(rect.left + rect.width / 2 - tooltipWidth / 2, window.innerWidth - tooltipWidth - 16))
                    };
                    break;

                case 'bottom':
                    newPosition = {
                        top: rect.bottom + gap,
                        left: Math.max(16, Math.min(rect.left + rect.width / 2 - tooltipWidth / 2, window.innerWidth - tooltipWidth - 16))
                    };
                    break;

                case 'left':
                    newPosition = {
                        top: Math.max(16, rect.top + rect.height / 2 - tooltipHeight / 2),
                        right: window.innerWidth - rect.left + gap
                    };
                    break;

                case 'right':
                    newPosition = {
                        top: Math.max(16, rect.top + rect.height / 2 - tooltipHeight / 2),
                        left: rect.right + gap
                    };
                    break;

                default:
                    newPosition = {
                        top: rect.bottom + gap,
                        left: Math.max(16, Math.min(rect.left, window.innerWidth - tooltipWidth - 16))
                    };
            }
        }

        setPosition(newPosition);
    };

    if (!currentStep || !isGuideActive || !isVisible) {
        return null;
    }

    // Add backdrop blur when tooltip is centered
    const isCentered = currentStep.position === 'center' || !currentStep.elementId;

    return (
        <>
            {/* Backdrop */}
            {isCentered && (
                <div 
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9998] animate-fade-in"
                    onClick={skipGuide}
                />
            )}

            {/* Spotlight effect for targeted elements */}
            {!isCentered && currentStep.elementId && (
                <div 
                    className="fixed inset-0 z-[9998] pointer-events-none"
                    style={{
                        background: 'radial-gradient(circle at var(--spotlight-x) var(--spotlight-y), transparent 100px, rgba(0,0,0,0.5) 200px)'
                    }}
                />
            )}

            {/* Tooltip */}
            <div
                ref={tooltipRef}
                className={`fixed z-[9999] bg-gradient-to-br from-blue-600 to-purple-600 text-white rounded-xl md:rounded-2xl shadow-2xl p-4 md:p-6 w-[calc(100%-2rem)] max-w-[320px] md:max-w-md animate-scale-in ${
                    isCentered ? 'transform -translate-x-1/2 -translate-y-1/2' : ''
                }`}
                style={position}
            >
                {/* Close Button */}
                <button
                    onClick={skipGuide}
                    className="absolute top-2 right-2 md:top-3 md:right-3 p-1 hover:bg-white/20 rounded-lg transition"
                    aria-label="Close guide"
                >
                    <X className="w-4 h-4 md:w-5 md:h-5" />
                </button>

                {/* Icon */}
                <div className="flex items-center gap-2 md:gap-3 mb-3 md:mb-4">
                    <div className="p-1.5 md:p-2 bg-white/20 rounded-lg">
                        <Sparkles className="w-4 h-4 md:w-6 md:h-6" />
                    </div>
                    <span className="text-xs md:text-sm font-semibold text-blue-100">
                        {t('guide.tip')}
                    </span>
                </div>

                {/* Content */}
                <div className="mb-4 md:mb-6">
                    <h3 className="text-base md:text-lg font-bold mb-1.5 md:mb-2 pr-6">
                        {t(`${currentStep.translationKey}.title`)}
                    </h3>
                    <p className="text-xs md:text-sm text-blue-50 leading-relaxed">
                        {t(`${currentStep.translationKey}.description`)}
                    </p>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between gap-2">
                    <button
                        onClick={skipGuide}
                        className="text-xs md:text-sm text-blue-100 hover:text-white transition"
                    >
                        {t('guide.skipTour')}
                    </button>
                    
                    <button
                        onClick={nextStep}
                        className="flex items-center gap-1.5 md:gap-2 px-3 md:px-4 py-1.5 md:py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition font-semibold text-xs md:text-sm"
                    >
                        {t('guide.next')}
                        <ChevronRight className="w-3 h-3 md:w-4 md:h-4" />
                    </button>
                </div>
            </div>

            <style>{`
                @keyframes fade-in {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                @keyframes scale-in {
                    from {
                        opacity: 0;
                        transform: scale(0.9) ${isCentered ? 'translate(-50%, -50%)' : ''};
                    }
                    to {
                        opacity: 1;
                        transform: scale(1) ${isCentered ? 'translate(-50%, -50%)' : ''};
                    }
                }

                .animate-fade-in {
                    animation: fade-in 0.2s ease-out;
                }

                .animate-scale-in {
                    animation: scale-in 0.3s ease-out;
                }
            `}</style>
        </>
    );
};

