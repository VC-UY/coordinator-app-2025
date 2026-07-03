import axios from 'axios';

const baseUrl = import.meta.env.PROD ? '/api/' : 'http://127.0.0.1:8001/api/'

const AxiosInstance = axios.create({
    baseURL: baseUrl,
    timeout: 30000,
    headers:{
        "Content-Type": "application/json",
        accept: "application/json"
    }
})

AxiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('coordinator_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default AxiosInstance;
