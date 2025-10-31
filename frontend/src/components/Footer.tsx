/**
 * Footer Component with Legal Links (Multilingual)
 * 
 * Displays legal links, copyright, and site information
 * Supports EN, RU, HE with proper RTL for Hebrew
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Footer.css';

const Footer: React.FC = () => {
    const { t, i18n } = useTranslation();
    const currentYear = new Date().getFullYear();
    const currentLang = i18n.language?.split('-')[0] || 'en';
    const isRTL = currentLang === 'he';

    return (
        <footer className={`footer ${isRTL ? 'footer--rtl' : ''}`} dir={isRTL ? 'rtl' : 'ltr'}>
            <div className="footer__container">
                {/* What's New Section - Subtle */}
                <div style={{
                    background: '#f3f4f6',
                    padding: '16px',
                    borderRadius: '8px',
                    marginBottom: '24px',
                    textAlign: 'center'
                }}>
                    <Link 
                        to="/whats-new"
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            color: '#6b7280',
                            textDecoration: 'none',
                            fontSize: '14px',
                            transition: 'color 0.2s'
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.color = '#4b5563';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.color = '#6b7280';
                        }}
                    >
                        <span>✨</span>
                        <span>{t("What's New")}</span>
                    </Link>
                </div>

                {/* Main Footer Content */}
                <div className="footer__content">
                    {/* Company Info */}
                    <div className="footer__section">
                        <h4 className="footer__heading">{t('footer.company')}</h4>
                        <nav className="footer__nav">
                            <Link to="/about" className="footer__link">
                                {t('footer.aboutUs')}
                            </Link>
                            <Link to="/whats-new" className="footer__link">
                                {t("What's New")}
                            </Link>
                            <Link to="/blog" className="footer__link">
                                {t('footer.blog')}
                            </Link>
                            <a href="https://github.com/menumindai" target="_blank" rel="noopener noreferrer" className="footer__link">
                                GitHub
                            </a>
                        </nav>
                    </div>

                    {/* Help & Support */}
                    <div className="footer__section">
                        <h4 className="footer__heading">{t('footer.support')}</h4>
                        <nav className="footer__nav">
                            <a href="mailto:support@menumindai.com" className="footer__link">
                                {t('footer.contactSupport')}
                            </a>
                            <a href="mailto:legal@menumindai.com" className="footer__link">
                                {t('footer.legalInquiries')}
                            </a>
                            <Link to="/settings" className="footer__link">
                                {t('footer.privacySettings')}
                            </Link>
                        </nav>
                    </div>

                    {/* Legal Links */}
                    <div className="footer__section">
                        <h4 className="footer__heading">{t('footer.legal')}</h4>
                        <nav className="footer__nav">
                            <Link to={`/legal/terms?lang=${currentLang}`} className="footer__link">
                                {t('footer.terms')}
                            </Link>
                            <Link to={`/legal/privacy?lang=${currentLang}`} className="footer__link">
                                {t('footer.privacy')}
                            </Link>
                            <Link to={`/legal/cookies?lang=${currentLang}`} className="footer__link">
                                {t('footer.cookies')}
                            </Link>
                            <Link to={`/legal/copyright?lang=${currentLang}`} className="footer__link">
                                {t('footer.copyright')}
                            </Link>
                            <Link to={`/legal/rcip?lang=${currentLang}`} className="footer__link">
                                {t('footer.rcipLicense')}
                            </Link>
                        </nav>
                    </div>

                    {/* Brand Section */}
                    <div className="footer__section footer__section--brand">
                        <h3 className="footer__title">MenuMindAI</h3>
                        <p className="footer__description">
                            {t('footer.description')}
                        </p>
                    </div>
                </div>

                {/* Compliance Notice */}
                <div className="footer__compliance">
                    <div className="footer__compliance-badges">
                        <div className="footer__badge" title={t('footer.israelCompliance')}>
                            <span className="footer__badge-icon">🇮🇱</span>
                            <span className="footer__badge-text">{t('footer.israelPPL')}</span>
                        </div>
                        <div className="footer__badge" title={t('footer.ccpaCompliance')}>
                            <span className="footer__badge-icon">🇺🇸</span>
                            <span className="footer__badge-text">{t('footer.ccpaCompliant')}</span>
                        </div>
                        <div className="footer__badge" title={t('footer.gdprCompliance')}>
                            <span className="footer__badge-icon">🇪🇺</span>
                            <span className="footer__badge-text">{t('footer.gdprCompliant')}</span>
                        </div>
                    </div>
                    <p className="footer__compliance-text">
                        {t('footer.complianceText')}
                    </p>
                </div>

                {/* Bottom Bar */}
                <div className="footer__bottom">
                    <div className="footer__bottom-links">
                        <Link to={`/legal/copyright?lang=${currentLang}`} className="footer__link">
                            {t('footer.licensing')}
                        </Link>
                        <span className="footer__divider">|</span>
                        <button
                            onClick={() => {
                                // Trigger cookie preferences modal
                                localStorage.removeItem('cookieConsent');
                                window.location.reload();
                            }}
                            className="footer__link footer__link--button"
                        >
                            {t('footer.cookiePreferences')}
                        </button>
                    </div>
                    <p className="footer__copyright">
                        {t('footer.copyrightText', { year: currentYear })}
                    </p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
