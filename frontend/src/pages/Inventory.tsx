import React from 'react';

const Inventory: React.FC = () => {
    return (
        <div className="max-w-7xl mx-auto p-6">
            <h2 className="text-3xl font-bold mb-6">Inventory Management</h2>
            <div className="bg-white rounded-lg shadow-lg p-12 text-center">
                <div className="text-6xl mb-4">📦</div>
                <h3 className="text-2xl font-semibold mb-2">Coming Soon!</h3>
                <p className="text-gray-600">
                    Track your pantry, fridge, and freezer items.<br />
                    Get alerts for expiring items and auto-generate shopping lists.
                </p>
            </div>
        </div>
    );
};

export default Inventory;



