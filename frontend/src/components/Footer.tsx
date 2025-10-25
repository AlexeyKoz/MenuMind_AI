import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { APP_VERSION } from '../config/version';

const Footer: React.FC = () => {
    const { t } = useTranslation();
    const currentYear = new Date().getFullYear();

    return (
        <footer className="bg-white border-t border-gray-200 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
                    {/* Left side - Copyright */}
                    <div className="text-sm text-gray-600">
                        © {currentYear} Alexey Kozlov. {t('footer.allRightsReserved')}
                    </div>

                    {/* Center - Links */}
                    <div className="flex items-center gap-4 text-sm">
                        <Link
                            to="/about"
                            className="text-gray-600 hover:text-blue-600 transition-colors"
                        >
                            {t('footer.about')}
                        </Link>
                        <Link
                            to="/settings"
                            className="text-gray-600 hover:text-blue-600 transition-colors"
                        >
                            {t('footer.settings')}
                        </Link>
                    </div>

                    {/* Right side - Version */}
                    <div className="text-sm text-gray-500 font-mono">
                        v{APP_VERSION}
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default Footer;

