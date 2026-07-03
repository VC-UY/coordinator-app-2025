import axios from 'axios';

// En production, utiliser /api/ (proxyed par nginx)
// En développement, utiliser l'URL complète du backend
const baseUrl = import.meta.env.PROD ? '/api/' : 'http://127.0.0.1:8001/'

const AxiosInstance = axios.create({
    baseURL: baseUrl,
    timeout: 30000, // Timeout augmenté pour les opérations longues
    headers:{
        "Content-Type": "application/json",
        accept: "application/json"
    }
})

export default AxiosInstance;