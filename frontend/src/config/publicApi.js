const publicApiConfig = {
  baseURL: process.env.VUE_APP_BACKEND_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};

export default publicApiConfig;