#!/bin/bash

echo "🧠 SmartNaggar AI - Quick Start Script"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "📦 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/uploads data/outputs models assets
touch data/uploads/.gitkeep data/outputs/.gitkeep
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Check for secrets
echo "🔐 Checking configuration..."
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo -e "${YELLOW}⚠️  No secrets file found!${NC}"
    echo "Please create .streamlit/secrets.toml with your credentials"
    echo "Template available in: .streamlit/secrets.toml.example"
    echo ""
    read -p "Do you want to create it now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p .streamlit
        cat > .streamlit/secrets.toml << 'EOL'
# Add your credentials here
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
EOL
        echo -e "${GREEN}✅ Secrets file created${NC}"
        echo "Please edit .streamlit/secrets.toml and add your credentials"
    fi
else
    echo -e "${GREEN}✅ Secrets file found${NC}"
fi
echo ""

# Final instructions
echo "======================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Setup Supabase:"
echo "   - Create account at supabase.com"
echo "   - Run setup_supabase.sql in SQL Editor"
echo "   - Add credentials to .streamlit/secrets.toml"
echo ""
echo "2. Run the application:"
echo "   ${YELLOW}streamlit run app.py${NC}"
echo ""
echo "3. Access admin dashboard:"
echo "   ${YELLOW}streamlit run pages/admin.py${NC}"
echo "   Credentials: admin / admin123"
echo ""
echo "📚 For more help, see README.md and DEPLOYMENT.md"
echo "======================================"