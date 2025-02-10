This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

### Environment Configuration

1. Copy the environment example file to create your local environment file:
   ```bash
   cp .env.example .env.local
   ```

2. Update the environment variables in `.env.local` as needed:
   - `NEXT_PUBLIC_API_URL`: The base URL for the API (defaults to http://hkapi.dailytoolset.com)

### Development Server

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

## Authentication

The application includes a complete authentication system with user registration and login functionality. For detailed documentation, see [Authentication Documentation](./docs/authentication.md).

### Features

- Secure user registration with password requirements
- User login with token-based authentication
- Form validation with real-time feedback
- Secure token storage using HTTP-only cookies
- Password strength validation
- Email format validation
- Username format validation

### Getting Started with Authentication

1. **User Registration**
   - Visit `/signup` to create a new account
   - Fill in required information:
     - Username (letters, numbers, underscores, hyphens)
     - Email (valid email format)
     - Password (meets security requirements)
     - Optional: Full Name

2. **User Login**
   - Visit `/login`
   - Enter credentials
   - Successful login redirects to dashboard

### Security Features

- Password requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character

- Secure token storage:
  - HTTP-only cookies
  - Secure flag in production
  - Strict same-site policy

For more detailed information about the authentication system, including API documentation, error handling, and troubleshooting, please refer to the [Authentication Documentation](./docs/authentication.md).

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.
