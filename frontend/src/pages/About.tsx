import React from 'react';
import { useTranslation } from 'react-i18next';

const About: React.FC = () => {
    const { t } = useTranslation();

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="bg-white rounded-lg shadow-lg p-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-6">
                        {t('about.title')}
                    </h1>

                    <div className="space-y-6 text-gray-700">
                        <section>
                            <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                                {t('about.whatIsMenuMineAI')}
                            </h2>
                            <p className="leading-relaxed">
                                {t('about.description')}
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                                {t('about.features')}
                            </h2>
                            <ul className="list-disc list-inside space-y-2">
                                <li>{t('about.feature1')}</li>
                                <li>{t('about.feature2')}</li>
                                <li>{t('about.feature3')}</li>
                                <li>{t('about.feature4')}</li>
                                <li>{t('about.feature5')}</li>
                            </ul>
                        </section>

                        <section>
                            <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                                {t('about.contact')}
                            </h2>
                            <p className="leading-relaxed">
                                {t('about.contactInfo')}
                            </p>
                        </section>

                        <section className="pt-6 border-t border-gray-200">
                            <p className="text-sm text-gray-500">
                                Version: 0.1.0
                            </p>
                            <p className="text-sm text-gray-500">
                                © {new Date().getFullYear()} Alexey Kozlov. {t('footer.allRightsReserved')}
                            </p>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default About;

