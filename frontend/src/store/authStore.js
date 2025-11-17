import { create } from 'zustand';
import { authAPI } from '../services/api';

export const useAuthStore = create((set) => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('token'),
    isAuthenticated: !!localStorage.getItem('token'),

    login: async(email, password) => {
        const response = await authAPI.login(email, password);
        const { access_token, user } = response.data;

        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));

        set({ token: access_token, user, isAuthenticated: true });
        return user;
    },

    register: async(data) => {
        const response = await authAPI.register(data);
        const { access_token, user } = response.data;

        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));

        set({ token: access_token, user, isAuthenticated: true });
        return user;
    },

    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        set({ token: null, user: null, isAuthenticated: false });
    },
}));