export { default as api } from './api';

export interface User {
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

    // ⬇️ ADD THESE TWO LINES:
    preferred_language?: 'en' | 'ru' | 'he';
    unit_system?: 'metric' | 'imperial';
}