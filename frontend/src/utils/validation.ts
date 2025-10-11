// Validation utilities - Simple validation without yup

// Simple validation functions
export const validateRequired = (value: string, fieldName: string): string | null => {
    if (!value || value.trim().length === 0) {
        return `${fieldName} is required`;
    }
    return null;
};

export const validateMinLength = (value: string, minLength: number, fieldName: string): string | null => {
    if (value.length < minLength) {
        return `${fieldName} must be at least ${minLength} characters`;
    }
    return null;
};

export const validateMaxLength = (value: string, maxLength: number, fieldName: string): string | null => {
    if (value.length > maxLength) {
        return `${fieldName} must be less than ${maxLength} characters`;
    }
    return null;
};

export const validateEmail = (email: string): string | null => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return 'Invalid email format';
    }
    return null;
};

export const validatePassword = (password: string): string | null => {
    if (password.length < 8) {
        return 'Password must be at least 8 characters';
    }
    if (!/(?=.*[a-z])/.test(password)) {
        return 'Password must contain at least one lowercase letter';
    }
    if (!/(?=.*[A-Z])/.test(password)) {
        return 'Password must contain at least one uppercase letter';
    }
    if (!/(?=.*\d)/.test(password)) {
        return 'Password must contain at least one number';
    }
    return null;
};

export const validatePasswordMatch = (password: string, confirmPassword: string): string | null => {
    if (password !== confirmPassword) {
        return 'Passwords must match';
    }
    return null;
};

// Login validation
export const validateLogin = (username: string, password: string): { username?: string; password?: string } => {
    const errors: { username?: string; password?: string } = {};

    const usernameError = validateRequired(username, 'Username') || validateMinLength(username, 3, 'Username');
    if (usernameError) errors.username = usernameError;

    const passwordError = validateRequired(password, 'Password') || validateMinLength(password, 6, 'Password');
    if (passwordError) errors.password = passwordError;

    return errors;
};

// Registration validation
export const validateRegistration = (data: {
    username: string;
    email: string;
    password: string;
    confirmPassword: string;
    firstName: string;
    lastName: string;
}): Record<string, string> => {
    const errors: Record<string, string> = {};

    const usernameError = validateRequired(data.username, 'Username') ||
        validateMinLength(data.username, 3, 'Username') ||
        validateMaxLength(data.username, 20, 'Username');
    if (usernameError) errors.username = usernameError;

    const emailError = validateRequired(data.email, 'Email') || validateEmail(data.email);
    if (emailError) errors.email = emailError;

    const passwordError = validateRequired(data.password, 'Password') || validatePassword(data.password);
    if (passwordError) errors.password = passwordError;

    const confirmPasswordError = validateRequired(data.confirmPassword, 'Confirm Password') ||
        validatePasswordMatch(data.password, data.confirmPassword);
    if (confirmPasswordError) errors.confirmPassword = confirmPasswordError;

    const firstNameError = validateRequired(data.firstName, 'First name') ||
        validateMinLength(data.firstName, 2, 'First name');
    if (firstNameError) errors.firstName = firstNameError;

    const lastNameError = validateRequired(data.lastName, 'Last name') ||
        validateMinLength(data.lastName, 2, 'Last name');
    if (lastNameError) errors.lastName = lastNameError;

    return errors;
};

// Type definitions for form data
export type LoginFormData = {
    username: string;
    password: string;
};

export type RegisterFormData = {
    username: string;
    email: string;
    password: string;
    confirmPassword: string;
    firstName: string;
    lastName: string;
};

export type ShoppingItemFormData = {
    name: string;
    quantity: number;
    unit: string;
    category: string;
};

export type NutritionEntryFormData = {
    meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    food_description: string;
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
};
