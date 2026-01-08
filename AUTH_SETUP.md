# Authentication Setup Guide

This guide explains how to set up and use the authentication system for Spark Playground.

## 🔐 Security Features

- **Password Hashing**: Passwords are hashed using bcrypt with automatic salt generation
- **JWT Tokens**: Secure JSON Web Tokens for session management
- **Email Validation**: Email addresses are validated on both frontend and backend
- **Input Sanitization**: Username validation (alphanumeric with _ and -)
- **Database Constraints**: Unique email and username enforcement

## 📦 Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `passlib[bcrypt]` - Password hashing with bcrypt
- `python-jose[cryptography]` - JWT token generation
- `email-validator` - Email validation

### 2. Configure Environment Variables

Create or update `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/spark_playground
SECRET_KEY=your-secret-key-here-use-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate a secure secret key:**
```bash
openssl rand -hex 32
```

### 3. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This will create the `users` table with the following schema:
- `id` (UUID) - Primary key
- `username` (String) - Unique username
- `email` (String) - Unique email
- `hashed_password` (String) - Bcrypt hashed password
- `is_active` (Boolean) - Account active status
- `is_verified` (Boolean) - Email verification status
- `created_at` (DateTime) - Account creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `last_login` (DateTime) - Last login timestamp

### 4. Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## 🎨 Frontend Setup

Frontend integration is already complete! The authentication pages are at:
- `/signin` - Sign in page
- `/signup` - Sign up page

## 🔌 API Endpoints

### POST `/api/auth/signup`
Register a new user

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-01T00:00:00",
    "last_login": "2024-01-01T00:00:00"
  }
}
```

### POST `/api/auth/signin`
Sign in an existing user

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response:** Same as signup

### GET `/api/auth/me`
Get current authenticated user (requires JWT token)

## 🧪 Testing the Authentication

### 1. Test Signup

```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. Test Signin

```bash
curl -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 3. Test with Frontend

1. Navigate to `http://localhost:5173/signup`
2. Fill in the form:
   - Username: testuser
   - Email: test@example.com
   - Password: password123
3. Click "Create Account"
4. You should be redirected to `/puzzles` upon success

## 🔒 Security Best Practices Implemented

1. **Password Hashing with Salt**
   - Using bcrypt algorithm
   - Automatic salt generation
   - Configurable cost factor (default: 12)

2. **JWT Token Security**
   - Short expiration time (30 minutes default)
   - Signed with secret key
   - Includes user ID and email in payload

3. **Input Validation**
   - Email format validation
   - Username alphanumeric check
   - Minimum password length (6 characters)
   - SQL injection prevention via SQLAlchemy ORM

4. **Database Security**
   - Unique constraints on email and username
   - Indexed fields for performance
   - Proper foreign key relationships

## 📝 Frontend Usage

The frontend automatically handles:
- Token storage in localStorage
- Token injection in API requests (via axios interceptor)
- Authentication state management
- Error handling and display

**Check if user is authenticated:**
```javascript
import { authService } from './services/api';

if (authService.isAuthenticated()) {
  const user = authService.getCurrentUser();
  console.log('Logged in as:', user.username);
}
```

**Sign out:**
```javascript
authService.signOut();
```

## 🐛 Troubleshooting

### "Email already registered"
- The email is already in use
- Try a different email or sign in instead

### "Username already taken"
- The username is already in use
- Choose a different username

### "Invalid email or password"
- Credentials don't match
- Check email and password

### Migration Error
```bash
# Reset migrations if needed
alembic downgrade base
alembic upgrade head
```

### JWT Token Issues
- Make sure SECRET_KEY is set in .env
- Check token expiration time
- Verify token is being sent in Authorization header

## 📚 API Documentation

Full API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🎯 Next Steps

Consider implementing:
1. Email verification system
2. Password reset functionality
3. OAuth providers (GitHub, Google)
4. Rate limiting on auth endpoints
5. Refresh token mechanism
6. Account deletion
7. Profile management
