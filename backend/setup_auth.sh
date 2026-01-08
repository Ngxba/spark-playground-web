#!/bin/bash

echo "🔐 Setting up Authentication System for Spark Playground"
echo "========================================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create a virtual environment first:"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    exit 1
fi

# Install dependencies
echo "📦 Installing authentication dependencies..."
pip install passlib[bcrypt]==1.7.4 python-jose[cryptography]==3.3.0 email-validator==2.1.0

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    SECRET_KEY=$(openssl rand -hex 32)
    cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/spark_playground
SECRET_KEY=${SECRET_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
    echo "✅ .env file created with generated SECRET_KEY"
else
    echo "⚠️  .env file already exists"
    if ! grep -q "SECRET_KEY" .env; then
        echo "⚙️  Adding SECRET_KEY to .env..."
        SECRET_KEY=$(openssl rand -hex 32)
        echo "" >> .env
        echo "SECRET_KEY=${SECRET_KEY}" >> .env
        echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env
        echo "✅ SECRET_KEY added to .env"
    else
        echo "✅ SECRET_KEY already configured"
    fi
fi

echo ""

# Run database migration
echo "🗄️  Running database migration..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Migration failed"
    echo "Make sure PostgreSQL is running and database exists"
    exit 1
fi

echo "✅ Database migration completed"
echo ""

echo "🎉 Authentication setup complete!"
echo ""
echo "Next steps:"
echo "1. Start the backend server:"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "2. Test the API at: http://localhost:8000/docs"
echo ""
echo "3. Navigate to http://localhost:5173/signup to create an account"
echo ""
