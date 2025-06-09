const publicApiConfig = {
  baseURL: process.env.VUE_APP_BACKEND_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};

export default publicApiConfig;