import axios from 'axios';
import publicApiConfig from '@/config/publicApi';

const publicApi = axios.create(publicApiConfig);

export default publicApi;