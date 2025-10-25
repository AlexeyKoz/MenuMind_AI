import React from 'react';

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error?: Error;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    handleReload = () => {
        this.setState({ hasError: false, error: undefined }, () => {
            window.location.reload();
        });
    };

    handleGoHome = () => {
        this.setState({ hasError: false, error: undefined }, () => {
            window.location.assign('/');
        });
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4 text-center">
                    <div className="max-w-md w-full bg-white shadow-lg rounded-xl p-8">
                        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Something went wrong</h1>
                        <p className="text-gray-600 mb-6">
                            We hit an unexpected issue while loading the page. You can refresh or head back to the dashboard.
                        </p>
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <pre className="bg-gray-100 text-left text-xs text-red-600 rounded-lg p-3 overflow-auto max-h-40 mb-4">
                                {this.state.error.message}
                            </pre>
                        )}
                        <div className="flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={this.handleReload}
                                className="flex-1 py-3 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition"
                            >
                                Refresh Page
                            </button>
                            <button
                                onClick={this.handleGoHome}
                                className="flex-1 py-3 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-100 transition"
                            >
                                Go to Dashboard
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
