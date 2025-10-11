import React from 'react';
import { useAuth } from '../contexts/AuthContext';

interface PrivateRouteProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({
    children,
    fallback = <div>Please log in to access this page.</div>
}) => {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!user) {
        return <>{fallback}</>;
    }

    return <>{children}</>;
};

export default PrivateRoute;
