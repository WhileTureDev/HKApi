# Authentication System Documentation

## Overview
The authentication system provides a secure, user-friendly way to handle user registration and login. It includes features like password strength validation, secure token storage, and proper error handling.

## Architecture

### Components
1. **Frontend Pages**
   - `/signup` - User registration page
   - `/login` - User authentication page

2. **API Routes**
   - `/api/auth/signup` - Handles user registration
   - `/api/auth/login` - Handles user authentication

3. **Utility Functions**
   - `validation.ts` - Contains validation logic for forms

## Features

### User Registration
- **Endpoint**: `POST /api/auth/signup`
- **Location**: `/app/api/auth/signup/route.ts`
- **Required Fields**:
  - username (string)
  - email (string)
  - password (string)
- **Optional Fields**:
  - full_name (string)
  - disabled (boolean)

#### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (!@#$%^&*)

### User Login
- **Endpoint**: `POST /api/auth/login`
- **Location**: `/app/api/auth/login/route.ts`
- **Required Fields**:
  - username (string)
  - password (string)

### Security Features

#### Token Storage
- Tokens are stored in HTTP-only cookies
- Cookie settings:
  ```typescript
  {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    path: '/',
    maxAge: 7200 // 2 hours
  }
  ```

#### Form Validation
- Real-time client-side validation
- Server-side validation for additional security
- Email format validation
- Password strength requirements
- Username format requirements

## Usage Examples

### User Registration
```typescript
// Example API call for user registration
const response = await fetch('/api/auth/signup', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'johndoe',
    full_name: 'John Doe',
    email: 'john@example.com',
    password: 'SecurePass123!'
  }),
});
```

### User Login
```typescript
// Example API call for user login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'johndoe',
    password: 'SecurePass123!'
  }),
});
```

## Error Handling

### Common Error Codes
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid credentials)
- `409` - Conflict (username/email already exists)
- `500` - Internal Server Error

### Error Response Format
```typescript
{
  error: string;
  details?: string[];
}
```

## Frontend Components

### Validation Utils
Location: `/app/utils/validation.ts`
```typescript
// Password validation
const passwordValidation = validatePassword(password);
if (!passwordValidation.isValid) {
  // Handle validation errors
  console.log(passwordValidation.errors);
}

// Email validation
const isValidEmail = validateEmail(email);

// Username validation
const usernameValidation = validateUsername(username);
if (!usernameValidation.isValid) {
  console.log(usernameValidation.error);
}
```

## User Flow

1. **Registration**:
   - User visits `/signup`
   - Fills out registration form
   - Form validates input in real-time
   - On success, redirects to `/login?registered=true`

2. **Login**:
   - User visits `/login`
   - Enters credentials
   - On success:
     - Receives authentication token in HTTP-only cookie
     - Redirects to `/dashboard`

## Future Enhancements

Planned features for future implementation:
1. Password recovery system
2. Remember me functionality
3. Social authentication integration
4. Multi-factor authentication
5. Session management
6. Account deletion
7. Password change functionality

## Maintenance

### Adding New Validation Rules
To add new validation rules, modify the validation utilities in `/app/utils/validation.ts`:

```typescript
export const validateNewField = (value: string): ValidationResult => {
  // Add validation logic here
  return {
    isValid: boolean,
    error?: string
  };
};
```

### Modifying Password Requirements
Password requirements can be adjusted in the `validatePassword` function in `/app/utils/validation.ts`.

### Updating Token Settings
Token settings can be modified in the login route handler at `/app/api/auth/login/route.ts`.

## Troubleshooting

Common issues and solutions:

1. **Login Failed**
   - Check if username/password are correct
   - Verify that cookies are enabled in the browser
   - Check if the token cookie is being set properly

2. **Registration Failed**
   - Verify that all required fields are provided
   - Check if the email/username is already in use
   - Ensure password meets all requirements

3. **Validation Errors**
   - Check browser console for detailed error messages
   - Verify that all form fields meet the requirements
   - Check network tab for API response details
