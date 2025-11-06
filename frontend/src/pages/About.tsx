import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Markdown from 'react-markdown';

interface AboutPageData {
    title: string;
    content: string;
    version: string;
    language: string;
    meta_description?: string;
    meta_keywords?: string;
    updated_at: string;
    fallback?: boolean;
}

const About: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [pageData, setPageData] = useState<AboutPageData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        loadAboutPage();
    }, [i18n.language]);  // Reload when language changes

    const loadAboutPage = async () => {
        try {
            setLoading(true);
            setError('');

            const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

            // Get current language (default to 'en')
            let userLang = i18n.language || 'en';
            // Handle language codes like 'en-US' -> 'en'
            userLang = userLang.split('-')[0].toLowerCase();
            // Ensure it's one of the supported languages
            if (!['en', 'ru', 'he'].includes(userLang)) {
                userLang = 'en';
            }

            const response = await fetch(`${apiUrl}/api/legal/about/?lang=${userLang}`);

            if (!response.ok) {
                throw new Error(`Failed to load about page: ${response.statusText}`);
            }

            const data = await response.json();
            setPageData(data);

            // If fallback occurred, show notice in console
            if (data.fallback) {
                console.warn(`About page not available in ${userLang}, showing English version`);
            }
        } catch (err) {
            console.error('Error loading about page:', err);
            setError(err instanceof Error ? err.message : 'Failed to load about page');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-white rounded-lg shadow-lg p-8">
                        <div className="flex justify-center items-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                            <p className="ml-4 text-gray-600">{t('common.loading')}</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-white rounded-lg shadow-lg p-8">
                        <div className="text-center py-12">
                            <h2 className="text-2xl font-bold text-red-600 mb-4">{t('common.error')}</h2>
                            <p className="text-gray-600 mb-4">{error}</p>
                            <button 
                                onClick={loadAboutPage}
                                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                            >
                                {t('common.retry') || 'Try Again'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (!pageData) {
        return (
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-white rounded-lg shadow-lg p-8">
                        <p className="text-center text-gray-600">{t('about.notFound') || 'About page not found'}</p>
                    </div>
                </div>
            </div>
        );
    }

    // Detect RTL for Hebrew
    const isRTL = pageData.language === 'he';
    const dir = isRTL ? 'rtl' : 'ltr';

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div 
                className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8"
                dir={dir}
                lang={pageData.language}
            >
                <div className="bg-white rounded-lg shadow-lg p-8">
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">
                            {pageData.title}
                        </h1>
                        {pageData.version && (
                            <p className="text-sm text-gray-500">
                                Version {pageData.version}
                            </p>
                        )}
                    </div>

                    <div 
                        className={`prose ${isRTL ? 'prose-rtl' : ''} max-w-none`}
                        style={{
                            fontFamily: isRTL ? '"Segoe UI", Tahoma, Arial, sans-serif' : 'inherit',
                            direction: dir
                        }}
                    >
                        <Markdown
                            components={{
                                h1: ({ ...props }) => <h2 className="text-2xl font-bold text-gray-900 mt-6 mb-4" {...props} />,
                                h2: ({ ...props }) => <h3 className="text-xl font-semibold text-gray-900 mt-5 mb-3" {...props} />,
                                h3: ({ ...props }) => <h4 className="text-lg font-semibold text-gray-900 mt-4 mb-2" {...props} />,
                                p: ({ ...props }) => <p className="text-gray-700 leading-relaxed mb-4" {...props} />,
                                ul: ({ ...props }) => <ul className="list-disc list-inside space-y-2 mb-4 text-gray-700" {...props} />,
                                ol: ({ ...props }) => <ol className="list-decimal list-inside space-y-2 mb-4 text-gray-700" {...props} />,
                                a: ({ ...props }) => <a className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer" {...props} />,
                                blockquote: ({ ...props }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4" {...props} />,
                            }}
                        >
                            {pageData.content}
                        </Markdown>
                    </div>

                    <div className="pt-6 mt-6 border-t border-gray-200">
                        <p className="text-sm text-gray-500">
                            {t('legalDocument.lastUpdated')} {new Date(pageData.updated_at).toLocaleDateString()}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default About;

