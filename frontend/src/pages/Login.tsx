import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface LoginProps {
    onLoginSuccess: () => void;
    onSwitchToRegistration?: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess, onSwitchToRegistration }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [copiedUser, setCopiedUser] = useState<string | null>(null);
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const result = await login(username, password);
        if (result.success) {
            onLoginSuccess();
        } else {
            setError(result.error || 'Login failed');
        }
    };

    const handleTestUserClick = (testUsername: string, testPassword: string) => {
        setUsername(testUsername);
        setPassword(testPassword);
        setCopiedUser(testUsername);
        setTimeout(() => setCopiedUser(null), 2000); // Clear the copied state after 2 seconds
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-xl p-8 w-96">
                <h2 className="text-3xl font-bold text-center mb-6">MenuMind AI</h2>
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            required
                        />
                    </div>
                    <div className="mb-6">
                        <label className="block text-sm font-medium mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            required
                        />
                    </div>
                    {error && (
                        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
                            {error}
                        </div>
                    )}
                    <button
                        type="submit"
                        className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                    >
                        Login
                    </button>
                </form>
                <div className="mt-6 p-4 bg-gray-50 rounded-lg border">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 text-center">🧪 Test Accounts</h3>
                    <div className="space-y-2">
                        <div
                            className={`flex justify-between items-center p-2 bg-white rounded border cursor-pointer hover:bg-blue-50 transition-colors ${copiedUser === 'testuser1' ? 'ring-2 ring-blue-400 bg-blue-50' : ''
                                }`}
                            onClick={() => handleTestUserClick('testuser1', 'password123')}
                        >
                            <span className="text-sm font-medium text-gray-600">User 1:</span>
                            <div className="text-sm">
                                <span className="font-mono text-blue-600">testuser1</span>
                                <span className="text-gray-400 mx-1">/</span>
                                <span className="font-mono text-green-600">password123</span>
                            </div>
                            {copiedUser === 'testuser1' && (
                                <span className="text-xs text-blue-600 ml-2">✓ Filled</span>
                            )}
                        </div>
                        <div
                            className={`flex justify-between items-center p-2 bg-white rounded border cursor-pointer hover:bg-blue-50 transition-colors ${copiedUser === 'testuser2' ? 'ring-2 ring-blue-400 bg-blue-50' : ''
                                }`}
                            onClick={() => handleTestUserClick('testuser2', 'password123')}
                        >
                            <span className="text-sm font-medium text-gray-600">User 2:</span>
                            <div className="text-sm">
                                <span className="font-mono text-blue-600">testuser2</span>
                                <span className="text-gray-400 mx-1">/</span>
                                <span className="font-mono text-green-600">password123</span>
                            </div>
                            {copiedUser === 'testuser2' && (
                                <span className="text-xs text-blue-600 ml-2">✓ Filled</span>
                            )}
                        </div>
                    </div>
                    <p className="text-xs text-gray-500 text-center mt-2">Click to fill login form</p>
                </div>

                {onSwitchToRegistration && (
                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-600">
                            Don't have an account?{' '}
                            <button
                                onClick={onSwitchToRegistration}
                                className="text-green-600 hover:text-green-700 font-medium"
                            >
                                Create account
                            </button>
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Login;