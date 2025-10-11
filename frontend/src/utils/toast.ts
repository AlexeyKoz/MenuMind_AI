import toast from 'react-hot-toast';

// Toast configuration
export const toastConfig = {
    position: "top-right" as const,
    duration: 5000,
};

// Success toast
export const showSuccess = (message: string) => {
    toast.success(message, toastConfig);
};

// Error toast
export const showError = (message: string) => {
    toast.error(message, toastConfig);
};

// Warning toast (using default toast with custom icon)
export const showWarning = (message: string) => {
    toast(message, { ...toastConfig, icon: '⚠️' });
};

// Info toast (using default toast with custom icon)
export const showInfo = (message: string) => {
    toast(message, { ...toastConfig, icon: 'ℹ️' });
};

// Loading toast
export const showLoading = (message: string) => {
    return toast.loading(message);
};

// Update loading toast
export const updateLoading = (toastId: string, message: string, type: 'success' | 'error' | 'warning' | 'info' = 'success') => {
    toast.dismiss(toastId);
    if (type === 'success') {
        toast.success(message, toastConfig);
    } else if (type === 'error') {
        toast.error(message, toastConfig);
    } else if (type === 'warning') {
        toast(message, { ...toastConfig, icon: '⚠️' });
    } else {
        toast(message, { ...toastConfig, icon: 'ℹ️' });
    }
};
