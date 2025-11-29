import axios from 'axios';

const API_BASE_URL =
    import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Get auth token from localStorage
const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

export const cameraService = {
    /**
     * Get list of all cameras
     * @returns {Promise<Array>} List of cameras with status
     */
    getCameras: async() => {
        try {
            const response = await axios.get(`${API_BASE_URL}/cameras`, {
                headers: getAuthHeader(),
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching cameras:', error);
            throw error;
        }
    },

    /**
     * Add a new camera
     * @param {string} cameraId - Unique camera identifier
     * @param {string} rtspUrl - RTSP URL or camera index (0 for webcam)
     * @returns {Promise<Object>} Response data
     */
    addCamera: async(cameraId, rtspUrl) => {
        try {
            const response = await axios.post(
                `${API_BASE_URL}/cameras/add`,
                null, {
                    params: {
                        camera_id: cameraId,
                        rtsp_url: rtspUrl,
                    },
                    headers: getAuthHeader(),
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error adding camera:', error);
            throw error;
        }
    },

    /**
     * Remove a camera
     * @param {string} cameraId - Camera identifier
     * @returns {Promise<Object>} Response data
     */
    removeCamera: async(cameraId) => {
        try {
            const response = await axios.delete(`${API_BASE_URL}/cameras/${cameraId}`, {
                headers: getAuthHeader(),
            });
            return response.data;
        } catch (error) {
            console.error('Error removing camera:', error);
            throw error;
        }
    },

    /**
     * Get camera info
     * @param {string} cameraId - Camera identifier
     * @returns {Promise<Object>} Camera status and metadata
     */
    getCameraInfo: async(cameraId) => {
        try {
            const response = await axios.get(`${API_BASE_URL}/cameras/${cameraId}/info`, {
                headers: getAuthHeader(),
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching camera info:', error);
            throw error;
        }
    },

    /**
     * Force reconnect a camera
     * @param {string} cameraId - Camera identifier
     * @returns {Promise<Object>} Response data
     */
    reconnectCamera: async(cameraId) => {
        try {
            const response = await axios.post(
                `${API_BASE_URL}/cameras/${cameraId}/reconnect`,
                null, {
                    headers: getAuthHeader(),
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error reconnecting camera:', error);
            throw error;
        }
    },

    /**
     * Get camera stream URL
     * @param {string} cameraId - Camera identifier
     * @param {boolean} detect - Enable detection
     * @param {boolean} alert - Enable alerts
     * @param {number} quality - JPEG quality (1-100)
     * @returns {string} Stream URL
     */
    getStreamUrl: (cameraId, detect = true, alert = true, quality = 80) => {
        const token = localStorage.getItem('token');
        const baseUrl = API_BASE_URL.replace('/api/v1', ''); // Remove /api/v1 for stream endpoint
        return `${baseUrl}/api/v1/cameras/${cameraId}/stream?detect=${detect}&alert=${alert}&quality=${quality}&token=${token}`;
    },
};

export const API_BASE_URL_EXPORT = API_BASE_URL;