import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

interface User {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    partner?: User;
    daily_calories_goal: number;
    daily_protein_goal: number;
    daily_carbs_goal: number;
    daily_fat_goal: number;
    preferred_language?: 'en' | 'ru' | 'he';
    unit_system?: 'metric' | 'imperial';
    allergies?: string[];
    temperature_unit?: 'celsius' | 'fahrenheit';
    email_verified?: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    loading: boolean;
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
    register: (username: string, email: string, password: string, firstName: string, lastName: string, preferredLanguage?: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);
    const apiBaseUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/?$/, '');
    const { i18n } = useTranslation();

    // Sync language when user changes
    useEffect(() => {
        if (user?.preferred_language && user.preferred_language !== i18n.language) {
            console.log(`🌐 Syncing language: ${i18n.language} → ${user.preferred_language}`);
            i18n.changeLanguage(user.preferred_language);
            localStorage.setItem('i18nextLng', user.preferred_language);
            document.documentElement.lang = user.preferred_language;
            document.documentElement.dir = user.preferred_language === 'he' ? 'rtl' : 'ltr';
        }
    }, [user?.preferred_language, i18n]);

    useEffect(() => {
        if (token) {
            fetchUserProfile();
        } else {
            setLoading(false);
        }
    }, [token]);

    const fetchUserProfile = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setLoading(false);
                return;
            }

            // Fetch user profile
            const profileResponse = await fetch(`${apiBaseUrl}/api/users/profile/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!profileResponse.ok) {
                throw new Error('Failed to fetch profile');
            }

            const profileResponseData = await profileResponse.json();

            // Extract user from paginated response
            const profileData = profileResponseData.results?.[0] || profileResponseData;

            // ⬇️ NEW: Fetch user preferences
            try {
                const prefsResponse = await fetch(`${apiBaseUrl}/api/users/profile/preferences/`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });

                if (prefsResponse.ok) {
                    const prefsData = await prefsResponse.json();

                    // Merge preferences into user object
                    setUser({
                        ...profileData,
                        preferred_language: prefsData.preferred_language,
                        unit_system: prefsData.unit_system,
                        email_verified: profileData?.email_verified ?? prefsData?.email_verified,
                    });

                    console.log('✅ User preferences loaded:', {
                        language: prefsData.preferred_language,
                        unit_system: prefsData.unit_system
                    });
                } else {
                    // If preferences don't exist yet, set user without them
                    setUser({
                        ...profileData,
                        email_verified: profileData?.email_verified,
                    });
                    console.log('⚠️ No preferences found, using defaults');
                }
            } catch (prefsError) {
                console.error('Failed to fetch preferences:', prefsError);
                // Still set user even if preferences fail
                setUser(profileData);
            }

        } catch (error) {
            console.error('Failed to fetch user profile:', error);
            localStorage.removeItem('token');
            localStorage.removeItem('refresh');
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
        try {
            console.log('🔐 Attempting login for:', username);
            const response = await fetch(`${apiBaseUrl}/api/users/auth/login/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            console.log('📡 Login response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Login successful, received data:', data);
                console.log('🌐 User preferred_language:', data.user?.preferred_language);
                setToken(data.access);
                setUser({
                    ...data.user,
                    email_verified: data?.user?.email_verified,
                    preferred_language: data?.user?.preferred_language
                });
                localStorage.setItem('token', data.access);
                localStorage.setItem('refresh', data.refresh);
                return { success: true };
            } else {
                const errorData = await response.text();
                console.log('❌ Login failed with response:', errorData);
                return { success: false, error: 'Invalid credentials' };
            }
        } catch (error) {
            console.error('🚨 Login error:', error);
            return { success: false, error: (error as Error).message };
        }
    };

    const register = async (username: string, email: string, password: string, firstName: string, lastName: string, preferredLanguage?: string): Promise<{ success: boolean; error?: string }> => {
        try {
            console.log('📝 Attempting registration for:', username);
            console.log('🌐 Preferred language:', preferredLanguage || 'en (default)');
            const response = await fetch(`${apiBaseUrl}/api/users/auth/register/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    first_name: firstName,
                    last_name: lastName,
                    preferred_language: preferredLanguage || 'en'
                })
            });

            console.log('📡 Registration response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Registration successful, received data:', data);
                setToken(data.access);
                setUser({
                    ...data.user,
                    preferred_language: preferredLanguage || data.user?.preferred_language || 'en'
                });
                localStorage.setItem('token', data.access);
                localStorage.setItem('refresh', data.refresh);
                return { success: true };
            } else {
                const errorData = await response.text();
                console.log('❌ Registration failed with response:', errorData);
                return { success: false, error: 'Registration failed' };
            }
        } catch (error) {
            console.error('🚨 Registration error:', error);
            return { success: false, error: (error as Error).message };
        }
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem('token');
        localStorage.removeItem('refresh');
    };

    return (
        <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};