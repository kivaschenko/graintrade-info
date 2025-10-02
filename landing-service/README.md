# Landing Service

This microservice provides multi-language landing pages for GrainTrade with how-to guides and FAQ sections.

## Features

- 🌐 Multi-language support (English/Ukrainian)
- 📱 Responsive design
- 🖼️ Image galleries with modal viewing
- 🔍 SEO optimized
- 🚀 Fast performance with caching
- 📊 Analytics ready
- ♿ Accessibility compliant

## Structure

```
landing-service/
├── app/
│   ├── main.py              # Flask application
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── how-to.html
│   │   └── faq.html
│   ├── static/              # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── locales/             # Language files
│       ├── en.json
│       └── uk.json
├── Dockerfile
├── requirements.txt
├── robots.txt
└── sitemap.xml
```

## Development

### Local Development

1. Install dependencies:
```bash
cd landing-service
pip install -r requirements.txt
```

2. Run the Flask app:
```bash
cd app
python main.py
```

3. Visit `http://localhost:8003`

### Docker Development

```bash
# Build the image
docker build -t graintrade-landing .

# Run the container
docker run -p 8003:8003 graintrade-landing
```

## Deployment

Use the deployment script:

```bash
# Deploy the Docker service
./deploy-landing.sh deploy

# Configure Apache (requires sudo)
sudo ./deploy-landing.sh apache

# Check health
./deploy-landing.sh health

# View logs
./deploy-landing.sh logs
```

## Language Support

The service supports dynamic language switching via URL parameter:
- English: `?lang=en`
- Ukrainian: `?lang=uk`

Language files are in JSON format in `app/locales/`.

## Apache Configuration

The service is designed to run behind Apache with:
- SSL termination
- Static file serving
- Gzip compression
- Security headers
- Rate limiting

## URLs

- Production: `https://home.graintrade.info` or `https://faq.graintrade.info`
- Development: `http://localhost:8003`

## API Endpoints

- `GET /` - Home page
- `GET /how-to` - How-to guide
- `GET /faq` - FAQ page
- `GET /health` - Health check

## Contributing

1. Update language files in `app/locales/`
2. Modify templates in `app/templates/`
3. Update styles in `app/static/css/`
4. Test locally before deployment
5. Use the deployment script for production

## Performance

- Static files served by Apache
- Gzip compression enabled
- Browser caching configured
- Image lazy loading
- CSS/JS minification

## Security

- HTTPS enforced
- Security headers configured
- Content Security Policy
- Rate limiting
- Input validation