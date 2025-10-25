import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { APP_VERSION, APP_BUILD_DATE, getVersionString } from '../config/version';

const Settings: React.FC = () => {
    const { t } = useTranslation();
    const [backendVersion, setBackendVersion] = useState<string>('');
    const [backendInfo, setBackendInfo] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch backend version
        const apiUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/?$/, '');

        fetch(`${apiUrl}/api/version/`)
            .then(response => response.json())
            .then(data => {
                setBackendVersion(data.version);
                setBackendInfo(data);
                setLoading(false);
            })
            .catch(error => {
                console.error('Failed to fetch backend version:', error);
                setLoading(false);
            });
    }, []);

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="bg-white rounded-lg shadow-lg p-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-6">
                        {t('settings.title')}
                    </h1>

                    <div className="space-y-6">
                        <div className="border-l-4 border-blue-500 pl-4 py-2 bg-blue-50">
                            <p className="text-blue-900">
                                {t('settings.comingSoon')}
                            </p>
                        </div>

                        <section>
                            <h2 className="text-xl font-semibold text-gray-900 mb-3">
                                {t('settings.plannedFeatures')}
                            </h2>
                            <ul className="list-disc list-inside space-y-2 text-gray-700">
                                <li>{t('settings.plannedFeature1')}</li>
                                <li>{t('settings.plannedFeature2')}</li>
                                <li>{t('settings.plannedFeature3')}</li>
                                <li>{t('settings.plannedFeature4')}</li>
                                <li>{t('settings.plannedFeature5')}</li>
                            </ul>
                        </section>

                        {/* Version Information Section */}
                        <section className="pt-6 border-t border-gray-200">
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">
                                {t('settings.aboutSection') || 'About'}
                            </h2>
                            <div className="bg-gray-50 rounded-lg p-6 space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="font-medium text-gray-700">Application:</span>
                                    <span className="text-gray-900">{getVersionString()}</span>
                                </div>

                                <div className="flex justify-between items-center">
                                    <span className="font-medium text-gray-700">Frontend Version:</span>
                                    <span className="text-gray-900 font-mono">v{APP_VERSION}</span>
                                </div>

                                {!loading && backendVersion && (
                                    <>
                                        <div className="flex justify-between items-center">
                                            <span className="font-medium text-gray-700">Backend Version:</span>
                                            <span className="text-gray-900 font-mono">v{backendVersion}</span>
                                        </div>

                                        {backendInfo && (
                                            <>
                                                <div className="flex justify-between items-center">
                                                    <span className="font-medium text-gray-700">Environment:</span>
                                                    <span className="text-gray-900 capitalize">{backendInfo.environment}</span>
                                                </div>

                                                <div className="flex justify-between items-center">
                                                    <span className="font-medium text-gray-700">API Version:</span>
                                                    <span className="text-gray-900">{backendInfo.api_version}</span>
                                                </div>
                                            </>
                                        )}
                                    </>
                                )}

                                {loading && (
                                    <div className="text-center text-gray-500 py-2">
                                        Loading backend info...
                                    </div>
                                )}

                                <div className="flex justify-between items-center">
                                    <span className="font-medium text-gray-700">Build Date:</span>
                                    <span className="text-gray-900">{APP_BUILD_DATE}</span>
                                </div>

                                <div className="pt-3 border-t border-gray-200">
                                    <div className="flex justify-between items-center">
                                        <span className="font-medium text-gray-700">Author:</span>
                                        <span className="text-gray-900">Alexey Kozlov</span>
                                    </div>
                                </div>
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;

