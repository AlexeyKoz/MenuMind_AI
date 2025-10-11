import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

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
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    loading: boolean;
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
    register: (username: string, email: string, password: string, firstName: string, lastName: string) => Promise<{ success: boolean; error?: string }>;
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

    useEffect(() => {
        if (token) {
            fetchUserProfile();
        } else {
            setLoading(false);
        }
    }, [token]);

    const fetchUserProfile = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/users/profile/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setUser(data.results?.[0] || data);
            } else {
                logout();
            }
        } catch (error) {
            console.error('Profile fetch error:', error);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
        try {
            console.log('🔐 Attempting login for:', username);
            const response = await fetch('http://localhost:8000/api/users/auth/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            console.log('📡 Login response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Login successful, received data:', data);
                setToken(data.access);
                setUser(data.user);
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

    const register = async (username: string, email: string, password: string, firstName: string, lastName: string): Promise<{ success: boolean; error?: string }> => {
        try {
            console.log('📝 Attempting registration for:', username);
            const response = await fetch('http://localhost:8000/api/users/auth/register/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    first_name: firstName,
                    last_name: lastName
                })
            });

            console.log('📡 Registration response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Registration successful, received data:', data);
                setToken(data.access);
                setUser(data.user);
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