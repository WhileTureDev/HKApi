# HKApi Frontend

A Django-based frontend application for managing Kubernetes API resources.

## Features

- Token-based authentication
- Project management dashboard
- Namespace management
- API key management
- Real-time metrics and monitoring

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` with your configuration:
```
API_URL=http://hkapi.dailytoolset.com
DEBUG=True
SECRET_KEY=your-secret-key
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver 0.0.0.0:3000
```

## Project Structure

```
frontend/
├── core/                   # Main application
│   ├── templates/         # HTML templates
│   ├── static/           # Static files (CSS, JS)
│   ├── views.py          # View controllers
│   └── urls.py           # URL routing
├── docs/                  # Documentation
│   └── dashboard_architecture.md
├── hkapi_ui/             # Project settings
└── requirements.txt      # Python dependencies
```

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions and classes

### Testing
Run tests with:
```bash
python manage.py test
```

### Documentation
- [Dashboard Architecture and Features](docs/dashboard_architecture.md)
- API documentation is available at `/api/docs/`
- Additional documentation can be found in the `docs/` directory

## API Integration

The frontend communicates with the HKApi backend using REST APIs:

- Authentication: `/api/v1/token`
- Projects: `/api/v1/projects/`
- Namespaces: `/api/v1/namespaces/`
- Metrics: `/api/v1/metrics/`

See the [API Documentation](docs/api.md) for detailed endpoint specifications.

## Security

- CSRF protection enabled
- Session-based authentication
- Token-based API authentication
- Rate limiting
- XSS protection

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team.
