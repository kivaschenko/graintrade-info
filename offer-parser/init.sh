#!/bin/bash
# Initialize data files for the parser

echo "Creating data directory and initializing domain vocabulary..."
python initialize_data.py

echo "Offer parser data initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Create .env file: cp .env.example .env"
echo "2. Configure LLM provider in .env"
echo "3. Run the service: python run.py"
echo ""
echo "API documentation will be available at http://localhost:8005/docs"
