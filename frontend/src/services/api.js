import axios from 'axios';

const API_BASE_URL =
    import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export const authAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (email, password) => {
        const formData = new FormData();
        formData.append('email', email);
        formData.append('password', password);
        return api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    getMe: () => api.get('/auth/me'),
};

export const detectionAPI = {
    detectImage: (file, confidence = 0.5, modelType = 'yolo') => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('confidence', confidence);
        formData.append('model_type', modelType);
        return api.post('/detection/detect/image', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    detectWeaponWithPairing: async(formData) => {
        const response = await api.post('/detection/detect/image-with-pairing', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },
    detectVideo: async(formData) => {
        const response = await api.post('/detection/detect/video', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 300000 // 5 minutes timeout for video processing
        });
        return response.data;
    },
    getModels: () => api.get('/detection/models'),
};

export const alertsAPI = {
    getAlerts: (params) => api.get('/alerts/', { params }),
    getAlertStats: (days = 7) => api.get('/alerts/stats', { params: { days } }),
    getAlert: (id) => api.get(`/alerts/${id}`),
    deleteAlert: (id) => api.delete(`/alerts/${id}`),
};

export default api;