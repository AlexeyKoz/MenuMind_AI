import React from 'react';
import { useAuth } from '../contexts/AuthContext';

interface NavigationProps {
    currentPage: string;
    setCurrentPage: (page: string) => void;
}

const Navigation: React.FC<NavigationProps> = ({ currentPage, setCurrentPage }) => {
    const { user, logout } = useAuth();

    const navItems = [
        { id: 'shopping', label: 'Shopping', icon: '🛒' },
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'nutrition', label: 'Nutrition', icon: '🥗' },
        { id: 'recipes', label: 'My Recipes', icon: '👨‍🍳' },
        { id: 'discover', label: 'Discover', icon: '🌟' },
        { id: 'inventory', label: 'Inventory', icon: '📦' },
        { id: 'archive', label: 'Archive', icon: '🗃️' },
        { id: 'settings', label: 'Settings', icon: '⚙️' }
    ];

    return (
        <nav className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-4 shadow-lg">
            <div className="max-w-7xl mx-auto flex justify-between items-center">
                <div className="flex items-center space-x-8">
                    <button
                        onClick={() => setCurrentPage('shopping')}
                        className="text-2xl font-bold hover:text-green-200 transition cursor-pointer"
                        title="Go to Home (Shopping Lists)"
                    >
                        🥗 MenuMind AI
                    </button>
                    <div className="flex space-x-6">
                        {navItems.map(item => (
                            <button
                                key={item.id}
                                onClick={() => setCurrentPage(item.id)}
                                className={`hover:text-green-200 transition ${currentPage === item.id ? 'text-green-200 font-bold' : ''
                                    }`}
                            >
                                {item.icon} {item.label}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="flex items-center space-x-4">
                    <span className="text-sm">👤 {user?.username}</span>
                    {user?.partner && <span className="text-sm">💑 Connected</span>}
                    <button
                        onClick={logout}
                        className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded transition"
                    >
                        Logout
                    </button>
                </div>
            </div>
        </nav>
    );
};

export default Navigation;