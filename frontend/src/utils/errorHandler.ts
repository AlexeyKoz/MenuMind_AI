/**
 * Utility functions for handling and formatting error messages
 */

export interface ApiError {
    error?: string;
    message?: string;
    detail?: string;
    non_field_errors?: string[];
    [key: string]: any;
}

/**
 * Extract a user-friendly error message from various error types
 */
export function getErrorMessage(error: any): string {
    // If it's already a simple string, return it
    if (typeof error === 'string') {
        return error;
    }

    // If it's an Error object, extract the message
    if (error instanceof Error) {
        return error.message;
    }

    // If it's an API error response object
    if (error && typeof error === 'object') {
        // Try common error message fields
        if (error.error && typeof error.error === 'string') {
            return error.error;
        }

        if (error.message && typeof error.message === 'string') {
            return error.message;
        }

        if (error.detail && typeof error.detail === 'string') {
            return error.detail;
        }

        // Handle Django REST framework validation errors
        if (error.non_field_errors && Array.isArray(error.non_field_errors)) {
            return error.non_field_errors.join(', ');
        }

        // Handle field-specific validation errors
        const fieldErrors = [];
        for (const [field, messages] of Object.entries(error)) {
            if (Array.isArray(messages) && field !== 'non_field_errors') {
                fieldErrors.push(`${field}: ${messages.join(', ')}`);
            }
        }

        if (fieldErrors.length > 0) {
            return fieldErrors.join('; ');
        }

        // If it's a complex object, try to stringify it safely
        try {
            const stringified = JSON.stringify(error);
            if (stringified && stringified !== '{}') {
                return `Error: ${stringified}`;
            }
        } catch {
            // JSON.stringify failed, fall through to default
        }
    }

    // Default fallback message
    return 'An unexpected error occurred';
}

/**
 * Sanitize error message to make it more user-friendly
 */
export function sanitizeErrorMessage(message: string): string {
    // Remove technical prefixes
    const cleanMessage = message
        .replace(/^API Error:\s*/i, '')
        .replace(/^Error:\s*/i, '')
        .replace(/^HTTP \d+ -?\s*/i, '');

    // Handle common API error patterns
    const patterns: [RegExp, string][] = [
        [/not found/i, 'Item not found'],
        [/unauthorized/i, 'You are not authorized to perform this action'],
        [/forbidden/i, 'Access denied'],
        [/bad request/i, 'Invalid request'],
        [/internal server error/i, 'Server error occurred'],
        [/network error/i, 'Network connection error'],
        [/timeout/i, 'Request timed out'],
        [/validation error/i, 'Invalid input provided'],
        [/permission denied/i, 'Permission denied'],
        [/not have permission/i, 'Permission denied'],
        [/cannot (add|edit|delete|invite)/i, 'Permission denied'],
        [/user not found/i, 'User not found'],
        [/already a collaborator/i, 'User is already a collaborator'],
        [/parameters.*wrong/i, 'Invalid parameters provided'],
        [/collaboration key/i, 'Invalid collaboration key'],
    ];

    for (const [pattern, replacement] of patterns) {
        if (pattern.test(cleanMessage)) {
            return replacement;
        }
    }

    // If it's too long, truncate it
    if (cleanMessage.length > 100) {
        return cleanMessage.substring(0, 97) + '...';
    }

    return cleanMessage || 'An error occurred';
}

/**
 * Get a user-friendly error message from any error type
 */
export function getUserFriendlyError(error: any): string {
    const rawMessage = getErrorMessage(error);
    return sanitizeErrorMessage(rawMessage);
}

/**
 * Show a user-friendly error toast
 */
export function showErrorToast(error: any, fallbackMessage?: string): void {
    const { toast } = require('react-hot-toast');
    const message = getUserFriendlyError(error) || fallbackMessage || 'An error occurred';
    toast.error(message);
}
