/**
 * Legal Document Viewer Component
 * 
 * Displays legal documents (Terms, Privacy, Cookies, etc.) from backend
 * Supports markdown rendering and multi-language (EN, RU, HE with RTL)
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Markdown from 'react-markdown';
import './LegalDocumentViewer.css';

interface LegalDocumentViewerProps {
    documentType: 'terms' | 'privacy' | 'cookies' | 'copyright' | 'rcip';
    title?: string;
}

interface DocumentData {
    content: string;
    version: string;
    effective_date: string;
    document_type: string;
    language?: string;
    fallback?: boolean;
}

const LegalDocumentViewer: React.FC<LegalDocumentViewerProps> = ({
    documentType,
    title
}) => {
    const { i18n } = useTranslation();
    const [document, setDocument] = useState<DocumentData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const documentTitles = {
        terms: 'Terms of Service',
        privacy: 'Privacy Policy',
        cookies: 'Cookie Policy',
        copyright: 'Copyright Notice',
        rcip: 'RCIP License'
    };

    useEffect(() => {
        loadDocument();
    }, [documentType, i18n.language]);  // Reload when language changes

    const loadDocument = async () => {
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

            const response = await fetch(`${apiUrl}/api/legal/${documentType}/?lang=${userLang}`);

            if (!response.ok) {
                throw new Error(`Failed to load document: ${response.statusText}`);
            }

            const data = await response.json();
            setDocument(data);

            // If fallback occurred, show notice in console
            if (data.fallback) {
                console.warn(`Legal document not available in ${userLang}, showing English version`);
            }
        } catch (err) {
            console.error('Error loading legal document:', err);
            setError(err instanceof Error ? err.message : 'Failed to load document');
        } finally {
            setLoading(false);
        }
    };

    const handlePrint = () => {
        window.print();
    };

    const handleDownload = () => {
        if (!document) return;

        const blob = new Blob([document.content], { type: 'text/markdown' });
        const url = window.URL.createObjectURL(blob);
        const link = window.document.createElement('a');
        link.href = url;
        link.download = `${documentType}-v${document.version}.md`;
        window.document.body.appendChild(link);
        link.click();
        window.document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    };

    if (loading) {
        return (
            <div className="legal-document">
                <div className="legal-document__loading">
                    <div className="legal-document__spinner"></div>
                    <p>Loading document...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="legal-document">
                <div className="legal-document__error">
                    <h2>Error Loading Document</h2>
                    <p>{error}</p>
                    <button onClick={loadDocument} className="legal-document__button">
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    if (!document) {
        return (
            <div className="legal-document">
                <div className="legal-document__error">
                    <p>Document not found</p>
                </div>
            </div>
        );
    }

    // Detect RTL for Hebrew
    const isRTL = document.language === 'he';
    const dir = isRTL ? 'rtl' : 'ltr';

    return (
        <div
            className={`legal-document ${isRTL ? 'legal-document--rtl' : ''}`}
            dir={dir}
            lang={document.language || 'en'}
        >
            <div className="legal-document__header">
                <div className="legal-document__header-content">
                    <h1 className="legal-document__title">
                        {title || documentTitles[documentType]}
                    </h1>
                    <div className="legal-document__meta">
                        <span className="legal-document__version">
                            Version {document.version}
                        </span>
                        <span className="legal-document__divider">•</span>
                        <span className="legal-document__date">
                            Effective {new Date(document.effective_date).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            })}
                        </span>
                    </div>
                </div>

                <div className="legal-document__actions">
                    <button
                        onClick={handlePrint}
                        className="legal-document__button legal-document__button--secondary"
                        aria-label="Print document"
                    >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M4 5V1H12V5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                            <path d="M4 11H2C1.44772 11 1 10.5523 1 10V7C1 6.44772 1.44772 6 2 6H14C14.5523 6 15 6.44772 15 7V10C15 10.5523 14.5523 11 14 11H12" stroke="currentColor" strokeWidth="1.5" />
                            <path d="M4 9H12V15H4V9Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Print
                    </button>

                    <button
                        onClick={handleDownload}
                        className="legal-document__button legal-document__button--secondary"
                        aria-label="Download document"
                    >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M8 1V11M8 11L11 8M8 11L5 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M1 11V14C1 14.5523 1.44772 15 2 15H14C14.5523 15 15 14.5523 15 14V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                        Download
                    </button>
                </div>
            </div>

            <div className="legal-document__content">
                <Markdown
                    components={{
                        h1: ({ ...props }) => <h2 className="legal-document__h2" {...props} />,
                        h2: ({ ...props }) => <h3 className="legal-document__h3" {...props} />,
                        h3: ({ ...props }) => <h4 className="legal-document__h4" {...props} />,
                        ul: ({ ...props }) => <ul className="legal-document__list" {...props} />,
                        ol: ({ ...props }) => <ol className="legal-document__list legal-document__list--ordered" {...props} />,
                        a: ({ ...props }) => <a className="legal-document__link" target="_blank" rel="noopener noreferrer" {...props} />,
                        blockquote: ({ ...props }) => <blockquote className="legal-document__blockquote" {...props} />,
                        table: ({ ...props }) => <table className="legal-document__table" {...props} />,
                    }}
                >
                    {document.content}
                </Markdown>
            </div>

            <div className="legal-document__footer">
                <p className="legal-document__footer-text">
                    Questions about this document?{' '}
                    <a href="mailto:legal@menumindai.com" className="legal-document__link">
                        Contact us at legal@menumindai.com
                    </a>
                </p>
                <p className="legal-document__footer-text legal-document__footer-text--small">
                    Last updated: {new Date(document.effective_date).toLocaleDateString()}
                </p>
            </div>
        </div>
    );
};

export default LegalDocumentViewer;

