# HKApi - Kubernetes API Management Platform

A comprehensive platform for managing Kubernetes API resources, providing both a FastAPI backend and a Django frontend interface.

## Project Overview

HKApi is designed to simplify Kubernetes API management through:
- Centralized project and namespace management
- Token-based authentication
- API key management
- Real-time metrics and monitoring
- Role-based access control

## Repository Structure

```
HKApi/
├── backend/              # FastAPI backend application
│   ├── api/             # API implementation
│   ├── tests/           # Backend tests
│   └── README.md        # Backend documentation
├── frontend/            # Django frontend application
│   ├── core/            # Main frontend app
│   ├── docs/            # Frontend documentation
│   └── README.md        # Frontend documentation
└── README.md            # This file
```

## Quick Start

1. Start the backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Start the frontend:
```bash
cd frontend
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:3000
```

For detailed setup instructions, see:
- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)

## Documentation

- [Backend API Documentation](backend/docs/api.md)
- [Frontend Dashboard Architecture](frontend/docs/dashboard_architecture.md)
- [Kubernetes Client Documentation](https://k8s-python.readthedocs.io/en/latest/)

## Contributing

Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

* **Catalin Radulescu** - *Initial work* - [cradules](https://github.com/cradules)
