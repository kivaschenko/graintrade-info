# Frontend Service - GrainTrade Web Application

[![Vue.js](https://img.shields.io/badge/Vue.js-3.5.13-4FC08D?style=flat&logo=vue.js)](https://vuejs.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3?style=flat&logo=bootstrap)](https://getbootstrap.com/)
[![Mapbox](https://img.shields.io/badge/Mapbox-GL_JS_3.8-000000?style=flat&logo=mapbox)](https://www.mapbox.com/)

## Overview

A modern, responsive Vue.js 3 web application providing the complete user interface for the GrainTrade agricultural trading platform. Built with performance and user experience in mind, featuring real-time chat, interactive maps, multilingual support, and comprehensive agricultural marketplace functionality.

## ✨ Features

### Core Functionality
- **🌾 Agricultural Marketplace**: Browse, search, and filter grain, seeds, fertilizers, and fuel offers
- **� Geospatial Search**: Interactive Mapbox integration with location-based filtering
- **💬 Real-time Chat**: WebSocket-powered messaging system for buyer-seller communication
- **👤 User Management**: Complete user profiles, authentication, and subscription management
- **💰 Payment Integration**: Seamless payment processing for premium features

### User Experience
- **🌍 Multilingual**: Ukrainian and English language support with Vue I18n
- **📱 Responsive Design**: Mobile-first approach with Bootstrap 5 responsive grid
- **🎨 Modern UI**: Clean, professional interface with Bootstrap Icons
- **⚡ Performance**: Single Page Application with optimized routing and lazy loading
- **♿ Accessibility**: WCAG compliant interface with proper ARIA labels

### Technical Features
- **🔐 Secure Authentication**: JWT-based authentication with automatic token refresh
- **� State Management**: Centralized state with Vuex for predictable data flow
- **📡 Real-time Updates**: WebSocket connections for live chat and notifications
- **🗂️ Component Architecture**: Reusable, maintainable Vue 3 components
- **🛡️ Error Handling**: Comprehensive error handling and user feedback

## 🛠️ Technology Stack

### Core Framework
- **Vue.js 3.5.13**: Latest Vue with Composition API and improved performance
- **Vue CLI 5.0.8**: Modern build tooling with Webpack
- **Vue Router 4.4.5**: Official router with dynamic imports and route guards
- **Vuex 4.1.0**: State management with modules and TypeScript support

### UI Framework & Styling
- **Bootstrap 5.3.3**: Responsive CSS framework with modern utilities
- **Bootstrap Icons 1.12.1**: Comprehensive icon library
- **Custom CSS**: Tailored styling for brand consistency

### Maps & Geolocation
- **Mapbox GL JS 3.8.0**: Interactive map rendering and visualization
- **Mapbox Geocoder 5.0.3**: Address search and geocoding functionality

### HTTP & Communication
- **Axios 1.7.7**: Promise-based HTTP client with interceptors
- **WebSocket**: Native WebSocket for real-time communication

### Internationalization & Utilities
- **Vue I18n 11.0.0**: Internationalization with pluralization and formatting
- **dotenv 16.4.5**: Environment variable management

### Build & Development
- **Babel**: ES6+ transpilation with modern preset
- **ESLint**: Code linting and formatting
- **Webpack**: Module bundling via Vue CLI

## 🏗️ Project Structure

```
frontend/
├── public/
│   ├── index.html              # Main HTML template
│   ├── favicon.ico            # Application favicon
│   └── icons/                 # PWA icons and assets
├── src/
│   ├── main.js                # Application entry point and Vue instance
│   ├── App.vue                # Root component with global layout
│   ├── components/            # Reusable Vue components
│   │   ├── ui/                # Generic UI components
│   │   ├── layout/            # Layout components (header, footer, etc.)
│   │   ├── forms/             # Form components and inputs
│   │   ├── maps/              # Map-related components
│   │   └── chat/              # Chat system components
│   ├── views/                 # Page-level route components
│   │   ├── Home.vue           # Landing page
│   │   ├── Items/             # Item listing and details
│   │   ├── Auth/              # Authentication pages
│   │   ├── Profile/           # User profile management
│   │   └── Chat/              # Chat interface
│   ├── router/                # Vue Router configuration
│   │   ├── index.js           # Main router setup
│   │   └── guards.js          # Route guards and middleware
│   ├── store/                 # Vuex store modules
│   │   ├── index.js           # Store root
│   │   ├── modules/           # Feature-specific store modules
│   │   │   ├── auth.js        # Authentication state
│   │   │   ├── items.js       # Item management
│   │   │   ├── chat.js        # Chat state
│   │   │   └── user.js        # User profile state
│   │   └── plugins/           # Store plugins and middleware
│   ├── services/              # API service layer
│   │   ├── api.js             # Main API client configuration
│   │   ├── authService.js     # Authentication API calls
│   │   ├── itemService.js     # Item management API
│   │   ├── chatService.js     # Chat API integration
│   │   └── mapService.js      # Geolocation and mapping
│   ├── utils/                 # Utility functions
│   │   ├── validators.js      # Form validation helpers
│   │   ├── formatters.js      # Data formatting utilities
│   │   ├── constants.js       # Application constants
│   │   └── helpers.js         # General helper functions
│   ├── locales/               # Internationalization files
│   │   ├── en.json            # English translations
│   │   └── uk.json            # Ukrainian translations
│   ├── assets/                # Static assets
│   │   ├── images/            # Image files
│   │   ├── icons/             # Icon assets
│   │   └── fonts/             # Custom fonts
│   └── styles/                # Global styling
│       ├── main.scss          # Main stylesheet
│       ├── variables.scss     # SCSS variables
│       ├── mixins.scss        # SCSS mixins
│       └── components.scss    # Component-specific styles
├── .env.example               # Environment variables template
├── .env.production            # Production environment config
├── package.json               # Dependencies and scripts
├── vue.config.js              # Vue CLI configuration
├── babel.config.js            # Babel transpilation config
├── jsconfig.json              # JavaScript/IDE configuration
├── nginx.conf                 # Production Nginx configuration
├── Dockerfile                 # Container configuration
└── README.md                  # This documentation
```

## 🚀 Quick Start

### Prerequisites
- **Node.js 16+**: Latest LTS version recommended
- **npm 8+**: Package manager
- **Backend API**: GrainTrade backend service running
- **Mapbox Account**: For mapping features

### 1. Environment Configuration

```bash
# Copy environment template
cp .env.example .env.local
```

Configure your `.env.local`:
```env
# API Endpoints
VUE_APP_API_BASE_URL=http://localhost:8000
VUE_APP_CHAT_API_URL=http://localhost:8001
VUE_APP_NOTIFICATIONS_API_URL=http://localhost:8002

# WebSocket Connections
VUE_APP_CHAT_WS_URL=ws://localhost:8001/ws
VUE_APP_NOTIFICATIONS_WS_URL=ws://localhost:8002/ws

# External Services
VUE_APP_MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token_here

# Application Settings
VUE_APP_DEFAULT_LANGUAGE=uk
VUE_APP_SUPPORTED_LANGUAGES=en,uk
VUE_APP_APP_NAME=GrainTrade
VUE_APP_CONTACT_EMAIL=support@graintrade.info

# Feature Flags
VUE_APP_ENABLE_CHAT=true
VUE_APP_ENABLE_MAPS=true
VUE_APP_ENABLE_PAYMENTS=true
```

### 2. Installation & Development

```bash
# Install dependencies
npm install

# Start development server
npm run serve

# Alternative: Development with hot reload
npm run dev
```

### 3. Access the Application

The application will be available at:
- **Development**: http://localhost:8080
- **Network Access**: Check terminal for network URL
## 📋 Available Scripts

```bash
# Development
npm run serve          # Start development server with hot reload
npm run dev           # Alternative development command

# Production
npm run build         # Build for production
npm run build:report  # Build with bundle analyzer report

# Code Quality
npm run lint          # Run ESLint
npm run lint:fix      # Fix ESLint issues automatically

# Dependencies
npm run deps:check    # Check for outdated packages
npm run deps:update   # Update dependencies
```

## ⚙️ Configuration

### Vue CLI Configuration (`vue.config.js`)

```javascript
const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,
  
  // Development server
  devServer: {
    port: 8080,
    host: '0.0.0.0',
    allowedHosts: 'all',
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_BASE_URL,
        changeOrigin: true,
        secure: false
      }
    }
  },
  
  // Build configuration
  productionSourceMap: false,
  filenameHashing: true,
  
  // Webpack optimization
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all'
          }
        }
      }
    }
  },
  
  // PWA configuration
  pwa: {
    name: 'GrainTrade',
    themeColor: '#4DBA87',
    msTileColor: '#000000',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'black'
  }
});
```

### Environment Configuration

#### Development (`.env.local`)
```env
VUE_APP_API_BASE_URL=http://localhost:8000
VUE_APP_CHAT_WS_URL=ws://localhost:8001/ws
VUE_APP_CHAT_HTTP_URL=http://localhost:8001
VUE_APP_MAPBOX_ACCESS_TOKEN=pk.your_dev_token
```

#### Production (`.env.production`)
```env
VUE_APP_API_BASE_URL=https://api.graintrade.info
VUE_APP_CHAT_WS_URL=wss://chat.graintrade.info/ws
VUE_APP_CHAT_HTTP_URL=https://chat.graintrade.info
VUE_APP_MAPBOX_ACCESS_TOKEN=pk.your_prod_token
VUE_APP_GA4_MEASUREMENT_ID=google-measurement-id-placeholder
VUE_APP_MS_CLARITY_PROJECT_ID=clarity-project-id-placeholder
```

## 🔗 Key Features Implementation

### Authentication System
```javascript
// store/modules/auth.js
export default {
  namespaced: true,
  
  state: {
    user: null,
    token: localStorage.getItem('token'),
    isAuthenticated: !!localStorage.getItem('token'),
    loading: false
  },
  
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    user: state => state.user,
    token: state => state.token
  },
  
  mutations: {
    SET_USER(state, user) {
      state.user = user;
      state.isAuthenticated = true;
    },
    
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem('token', token);
      state.isAuthenticated = true;
    },
    
    LOGOUT(state) {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      localStorage.removeItem('token');
    }
  },
  
  actions: {
    async login({ commit }, credentials) {
      try {
        const response = await authService.login(credentials);
        commit('SET_TOKEN', response.data.access_token);
        commit('SET_USER', response.data.user);
        return response.data;
      } catch (error) {
        throw error;
      }
    },
    
    logout({ commit }) {
      commit('LOGOUT');
      router.push('/login');
    }
  }
};
```

### Mapbox Integration
```vue
<!-- components/MapComponent.vue -->
<template>
  <div class="map-wrapper">
    <div id="map" class="map-container" :style="{ height: mapHeight }"></div>
    <div v-if="loading" class="map-loading">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading map...</span>
      </div>
    </div>
  </div>
</template>

<script>
import mapboxgl from 'mapbox-gl';
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';

export default {
  name: 'MapComponent',
  
  props: {
    items: {
      type: Array,
      default: () => []
    },
    center: {
      type: Array,
      default: () => [30.5234, 50.4501] // Kyiv coordinates
    },
    zoom: {
      type: Number,
      default: 8
    },
    mapHeight: {
      type: String,
      default: '400px'
    }
  },
  
  data() {
    return {
      map: null,
      loading: true,
      markers: []
    };
  },
  
  mounted() {
    this.initializeMap();
  },
  
  beforeUnmount() {
    if (this.map) {
      this.map.remove();
    }
  },
  
  watch: {
    items: {
      handler: 'updateMarkers',
      deep: true
    }
  },
  
  methods: {
    initializeMap() {
      mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_ACCESS_TOKEN;
      
      this.map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: this.center,
        zoom: this.zoom
      });
      
      // Add controls
      this.map.addControl(new mapboxgl.NavigationControl());
      this.map.addControl(
        new MapboxGeocoder({
          accessToken: mapboxgl.accessToken,
          mapboxgl: mapboxgl,
          placeholder: this.$t('map.search_placeholder')
        })
      );
      
      this.map.on('load', () => {
        this.loading = false;
        this.updateMarkers();
      });
    },
    
    updateMarkers() {
      // Clear existing markers
      this.markers.forEach(marker => marker.remove());
      this.markers = [];
      
      // Add new markers
      this.items.forEach(item => {
        if (item.latitude && item.longitude) {
          const marker = new mapboxgl.Marker()
            .setLngLat([item.longitude, item.latitude])
            .setPopup(
              new mapboxgl.Popup().setHTML(`
                <div class="map-popup">
                  <h6>${item.title}</h6>
                  <p>${item.description}</p>
                  <p><strong>${item.price} ${item.currency}</strong></p>
                </div>
              `)
            )
            .addTo(this.map);
            
          this.markers.push(marker);
        }
      });
    }
  }
};
</script>

<style scoped>
.map-wrapper {
  position: relative;
}

.map-container {
  width: 100%;
  border-radius: 8px;
}

.map-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1000;
}

:deep(.mapboxgl-popup-content) {
  padding: 15px;
  border-radius: 8px;
}

:deep(.map-popup h6) {
  margin-bottom: 8px;
  color: #333;
}
</style>
```

### Real-time Chat Integration
```javascript
// services/chatService.js
class ChatService {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000;
    this.messageQueue = [];
  }
  
  connect(roomId, token) {
    const wsUrl = `${process.env.VUE_APP_CHAT_WS_URL}/${roomId}?token=${token}`;
    
    try {
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = () => {
        console.log('Chat connected to room:', roomId);
        this.reconnectAttempts = 0;
        this.flushMessageQueue();
      };
      
      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };
      
      this.socket.onclose = (event) => {
        console.log('Chat disconnected:', event.code, event.reason);
        this.attemptReconnect(roomId, token);
      };
      
      this.socket.onerror = (error) => {
        console.error('Chat WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Error connecting to chat:', error);
    }
  }
  
  sendMessage(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      // Queue message for when connection is restored
      this.messageQueue.push(message);
    }
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
  
  attemptReconnect(roomId, token) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect(roomId, token);
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
  
  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.sendMessage(message);
    }
  }
  
  handleMessage(message) {
    // Emit message to store or event bus
    if (window.Vue && window.Vue.config.globalProperties.$store) {
      window.Vue.config.globalProperties.$store.dispatch('chat/addMessage', message);
    }
  }
}

export default new ChatService();
```

## 🚀 Deployment

### Docker Production Build

```dockerfile
# Dockerfile
FROM node:18-alpine as build-stage

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine as production-stage

# Copy build files
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration
```nginx
# nginx.conf
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        application/atom+xml
        application/javascript
        application/json
        application/rss+xml
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-web-app-manifest+json
        application/xhtml+xml
        application/xml
        font/opentype
        image/svg+xml
        image/x-icon
        text/css
        text/plain
        text/x-component;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # Static assets caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Handle SPA routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### Production Deployment Commands

```bash
# Build production image
docker build -t graintrade-frontend:latest .

# Run container
docker run -d \
  --name graintrade-frontend \
  -p 80:80 \
  graintrade-frontend:latest

# Using Docker Compose
docker-compose up -d frontend
```

## 📊 Performance & Optimization

### Bundle Analysis
```bash
# Install analyzer
npm install --save-dev webpack-bundle-analyzer

# Generate report
npm run build -- --report

# Analyze specific bundles
npx webpack-bundle-analyzer dist/static/js/*.js
```

### Performance Optimizations
- **Code Splitting**: Route-based and component-based splitting
- **Lazy Loading**: Components and routes loaded on demand
- **Tree Shaking**: Eliminate dead code
- **Image Optimization**: WebP format, lazy loading
- **Service Worker**: Caching strategies for offline support
- **Critical CSS**: Inline critical CSS for faster rendering

### SEO & Meta Tags
```javascript
// router/index.js - Meta tags per route
{
  path: '/',
  name: 'Home',
  component: () => import('@/views/Home.vue'),
  meta: {
    title: 'GrainTrade - Agricultural Trading Platform',
    description: 'Trade agricultural commodities in Ukraine',
    keywords: 'grain, trade, agriculture, ukraine'
  }
}
```

## 🧪 Testing

### Testing Setup (Future Implementation)
```bash
# Install testing dependencies
npm install --save-dev @vue/test-utils jest @testing-library/vue

# Run tests
npm run test:unit

# Watch mode
npm run test:unit -- --watch

# Coverage report
npm run test:unit -- --coverage
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install dependencies: `npm install`
4. Follow Vue.js style guide and ESLint rules
5. Test your changes thoroughly
6. Update documentation as needed
7. Submit a pull request

### Development Guidelines
- **Vue 3 Composition API**: Prefer Composition API for new components
- **TypeScript**: Consider TypeScript for complex components
- **Component Structure**: Single-file components with clear separation
- **Props Validation**: Always validate props with proper types
- **Event Naming**: Use kebab-case for custom events
- **Styling**: Use scoped styles and CSS modules

## 🌐 Browser Support

- **Chrome**: 88+
- **Firefox**: 85+
- **Safari**: 14+
- **Edge**: 88+
- **Mobile Safari**: iOS 14+
- **Chrome Mobile**: Android 88+

## 📄 License

This project is licensed under the MIT - see the [LICENSE](../LICENSE) file for details.

## 📧 Support

For support and questions:
- **Email**: kivaschenko@protonmail.com
- **Issues**: [GitHub Issues](https://github.com/kivaschenko/graintrade-info/issues)
- **Documentation**: [Project Wiki](https://github.com/kivaschenko/graintrade-info/wiki)

---

**Part of the GrainTrade platform** 🌾
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
