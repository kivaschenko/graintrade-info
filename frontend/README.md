# Frontend Service - GrainTrade Web Application

## Overview
The Frontend service is a modern Vue.js 3 web application that provides the user interface for the GrainTrade platform. It offers an intuitive interface for agricultural market participants to browse offers, manage their listings, communicate through chat, and interact with geographical mapping features.

## Features
- 🌾 **Agricultural Market Interface**: Browse and filter agricultural offers
- 🗺️ **Interactive Maps**: Mapbox integration for geographical visualization
- 💬 **Real-time Chat**: WebSocket-based messaging with other users
- 🔐 **User Authentication**: Secure login and user management
- 🌍 **Internationalization**: Multi-language support with Vue I18n
- 📱 **Responsive Design**: Mobile-first responsive interface with Bootstrap 5
- 🎨 **Modern UI**: Clean, professional interface with Bootstrap Icons
- 🔄 **State Management**: Centralized state management with Vuex
- 🚀 **Performance Optimized**: Single Page Application with optimized routing

## Technology Stack
- **Framework**: Vue.js 3.5.13
- **Build Tool**: Vue CLI 5.0.8
- **Styling**: Bootstrap 5.3.3 + Bootstrap Icons
- **Maps**: Mapbox GL JS 3.8.0 + Geocoder
- **HTTP Client**: Axios 1.7.7
- **Routing**: Vue Router 4.4.5
- **State Management**: Vuex 4.1.0
- **Internationalization**: Vue I18n 11.0.0-beta.1
- **JavaScript**: ES6+ with Babel compilation
- **Development**: Hot reload, ESLint integration

## Project Structure
```
frontend/
├── public/
│   ├── index.html           # Main HTML template
│   ├── favicon.ico         # Application favicon
│   └── assets/             # Static assets
├── src/
│   ├── main.js             # Application entry point
│   ├── App.vue             # Root Vue component
│   ├── components/         # Reusable Vue components
│   ├── views/              # Page-level Vue components
│   ├── router/             # Vue Router configuration
│   ├── store/              # Vuex store modules
│   ├── services/           # API service layer
│   ├── utils/              # Utility functions
│   ├── locales/            # Internationalization files
│   ├── assets/             # Images, styles, static files
│   └── styles/             # Global CSS/SCSS files
├── package.json            # NPM dependencies and scripts
├── vue.config.js           # Vue CLI configuration
├── babel.config.js         # Babel configuration
├── jsconfig.json           # JavaScript configuration
├── nginx.conf              # Nginx configuration for production
└── Dockerfile              # Docker container configuration
```

## Quick Start

### Prerequisites
- Node.js 16+ and npm
- Access to backend API
- Mapbox API token (for map features)

### 1. Environment Setup
Create environment configuration:
```bash
# Create environment file
cp .env.example .env.local
```

Configure `.env.local`:
```env
# API Configuration
VUE_APP_API_BASE_URL=http://localhost:8000
VUE_APP_CHAT_WS_URL=ws://localhost:8001
VUE_APP_NOTIFICATIONS_URL=http://localhost:8002

# Mapbox Configuration
VUE_APP_MAPBOX_ACCESS_TOKEN=your_mapbox_token_here

# Application Configuration
VUE_APP_NAME=GrainTrade
VUE_APP_VERSION=1.0.0
VUE_APP_ENVIRONMENT=development
```

### 2. Install Dependencies
```bash
cd frontend
npm install
```

### 3. Development Setup

#### Local Development Server
```bash
# Start development server with hot reload
npm run serve
```
The application will be available at `http://localhost:8080`

#### Production Build
```bash
# Build for production
npm run build
```
Built files will be in the `dist/` directory.

### 4. Development Tools
```bash
# Lint and fix files
npm run lint

# Run specific linting rules
npm run lint -- --fix
```

## Configuration

### Vue CLI Configuration (`vue.config.js`)
```javascript
module.exports = {
  // Webpack configuration
  configureWebpack: {
    // Custom webpack settings
  },
  
  // Development server configuration
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_BASE_URL,
        changeOrigin: true
      }
    }
  },
  
  // Build configuration
  productionSourceMap: false,
  
  // PWA configuration
  pwa: {
    // PWA settings
  }
}
```

### Babel Configuration (`babel.config.js`)
```javascript
module.exports = {
  presets: [
    '@vue/cli-plugin-babel/preset'
  ],
  plugins: [
    // Babel plugins
  ]
}
```

## Key Features Implementation

### 1. Authentication System
```javascript
// store/modules/auth.js
export default {
  state: {
    user: null,
    token: localStorage.getItem('token'),
    isAuthenticated: false
  },
  
  mutations: {
    SET_USER(state, user) {
      state.user = user;
      state.isAuthenticated = true;
    },
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem('token', token);
    }
  },
  
  actions: {
    async login({ commit }, credentials) {
      const response = await authService.login(credentials);
      commit('SET_TOKEN', response.data.token);
      commit('SET_USER', response.data.user);
    }
  }
}
```

### 2. Mapbox Integration
```javascript
// components/MapComponent.vue
<template>
  <div id="map" class="map-container"></div>
</template>

<script>
import mapboxgl from 'mapbox-gl';
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';

export default {
  name: 'MapComponent',
  
  mounted() {
    mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_ACCESS_TOKEN;
    
    this.map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [30.5234, 50.4501], // Kyiv coordinates
      zoom: 8
    });
    
    // Add geocoder control
    this.map.addControl(
      new MapboxGeocoder({
        accessToken: mapboxgl.accessToken,
        mapboxgl: mapboxgl
      })
    );
  }
}
</script>
```

### 3. Real-time Chat Integration
```javascript
// services/chatService.js
class ChatService {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  connect(roomId) {
    const wsUrl = `${process.env.VUE_APP_CHAT_WS_URL}/ws/${roomId}`;
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onopen = () => {
      console.log('Chat connected');
      this.reconnectAttempts = 0;
    };
    
    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.$store.dispatch('chat/addMessage', message);
    };
    
    this.socket.onclose = () => {
      this.reconnect(roomId);
    };
  }
  
  sendMessage(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }
}
```

### 4. Internationalization
```javascript
// locales/en.json
{
  "nav": {
    "home": "Home",
    "offers": "Offers",
    "chat": "Chat",
    "profile": "Profile"
  },
  "offers": {
    "title": "Agricultural Offers",
    "filter": "Filter offers",
    "location": "Location",
    "category": "Category",
    "price": "Price"
  }
}

// locales/uk.json
{
  "nav": {
    "home": "Головна",
    "offers": "Пропозиції",
    "chat": "Чат",
    "profile": "Профіль"
  },
  "offers": {
    "title": "Сільськогосподарські пропозиції",
    "filter": "Фільтрувати пропозиції",
    "location": "Місцезнаходження",
    "category": "Категорія",
    "price": "Ціна"
  }
}
```

## API Integration

### HTTP Client Configuration
```javascript
// services/api.js
import axios from 'axios';
import store from '@/store';

const api = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL,
  timeout: 10000
});

// Request interceptor for authentication
api.interceptors.request.use(
  config => {
    const token = store.getters['auth/token'];
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      store.dispatch('auth/logout');
    }
    return Promise.reject(error);
  }
);

export default api;
```

## Deployment

### Docker Production Build
```bash
# Build the image
docker build -t graintrade-frontend:latest .

# Run the container
docker run -p 80:80 graintrade-frontend:latest
```

### Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.yaml up frontend -d
```

### Nginx Configuration
The included `nginx.conf` provides:
- Static file serving
- Gzip compression
- SPA routing support
- Security headers
- Caching policies

### Environment Variables for Production
```env
VUE_APP_API_BASE_URL=https://api.graintrade.info
VUE_APP_CHAT_WS_URL=wss://chat.graintrade.info
VUE_APP_NOTIFICATIONS_URL=https://notifications.graintrade.info
VUE_APP_MAPBOX_ACCESS_TOKEN=your_production_mapbox_token
VUE_APP_ENVIRONMENT=production
```

## Performance Optimization

### Build Optimization
- **Code Splitting**: Automatic route-based code splitting
- **Tree Shaking**: Remove unused code from bundles
- **Asset Optimization**: Image and asset compression
- **Minification**: JavaScript and CSS minification

### Runtime Optimization
- **Lazy Loading**: Lazy load components and routes
- **Virtual Scrolling**: For large lists (offers, messages)
- **Image Lazy Loading**: Load images on demand
- **Caching**: HTTP response caching and local storage

### Bundle Analysis
```bash
# Analyze bundle size
npm run build -- --analyze

# Generate bundle report
npm install -g webpack-bundle-analyzer
webpack-bundle-analyzer dist/static/js/*.js
```

## Testing

### Unit Testing (Future Implementation)
```bash
# Install testing dependencies
npm install --save-dev @vue/test-utils jest vue-jest

# Run unit tests
npm run test:unit

# Run tests with coverage
npm run test:unit -- --coverage
```

### End-to-End Testing (Future Implementation)
```bash
# Install E2E testing dependencies
npm install --save-dev cypress

# Run E2E tests
npm run test:e2e
```

## Development Guidelines

### Component Structure
```vue
<template>
  <!-- Template with semantic HTML -->
</template>

<script>
export default {
  name: 'ComponentName',
  
  components: {
    // Local components
  },
  
  props: {
    // Component props with validation
  },
  
  data() {
    return {
      // Component state
    };
  },
  
  computed: {
    // Computed properties
  },
  
  methods: {
    // Component methods
  },
  
  // Lifecycle hooks
  created() {},
  mounted() {},
  beforeDestroy() {}
}
</script>

<style scoped>
/* Component-specific styles */
</style>
```

### Code Style
- Use Vue 3 Composition API for complex components
- Follow Vue.js style guide recommendations
- Use semantic HTML elements
- Implement proper accessibility (ARIA labels, roles)
- Use TypeScript for type safety (future enhancement)

### State Management Best Practices
- Keep state minimal and normalized
- Use getters for computed state
- Implement proper action/mutation patterns
- Handle asynchronous operations in actions

## Troubleshooting

### Common Issues

1. **Build Fails**
   ```bash
   # Clear node modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Map Not Loading**
   - Verify Mapbox access token
   - Check browser console for API errors
   - Ensure proper CORS configuration

3. **WebSocket Connection Issues**
   - Check WebSocket URL configuration
   - Verify backend chat service is running
   - Check for proxy configuration in development

4. **Authentication Problems**
   - Verify API base URL
   - Check token storage and retrieval
   - Ensure proper CORS headers from backend

## Browser Support
- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

## Contributing
1. Fork the repository
2. Create a feature branch
3. Follow Vue.js and project coding standards
4. Test your changes thoroughly
5. Submit a pull request

## License
Apache-2.0 License

## Support
For support and questions, contact: kivaschenko@protonmail.com
