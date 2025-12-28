# Walet Main Service (Backend)

## Team Members

**Group Name:** Tanya Steven (TS)

| Name | NPM |
|------|-----|
| Naufal Ichsan | 2206082013 |
| Winoto Hasyim | 2206025243 |
| Steven Faustin Orginata | 2206030855 |
| Matthew Hotmaraja Johan Turnip | 2206081231 |
| Emir Mohamad Fathan | 2206081982 |

---

The backend service for Walet - a wallet/finance management system. This project handles data persistence, business logic, and authentication for the Walet ecosystem. It is built with Django and Django REST Framework, containerized with Docker, and orchestrates a PostgreSQL database.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Deployment Guide](#deployment-guide)
- [Project Architecture](#project-architecture)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

This repository contains the **backend** portion of the Walet application. It provides a RESTful API consumed by the frontend, managing:

- **Authentication:** JWT-based user authentication (Login, Register).
- **Funds Management:** Logic for wallet balances and transactions.
- **Project Management:** Handling project data, collaborations, and invitations.
- **Data Persistence:** Storing all application data in a PostgreSQL database.

---

## Tech Stack

| Category | Technology | Version |
|----------|------------|---------|
| **Framework** | [Django](https://www.djangoproject.com/) | 5.1.6 |
| **API Toolkit** | [Django REST Framework](https://www.django-rest-framework.org/) | 3.x |
| **Runtime** | [Python](https://www.python.org/) | 3.13-slim |
| **Database** | [PostgreSQL](https://www.postgresql.org/) | 15-alpine |
| **WSGI Server** | [Gunicorn](https://gunicorn.org/) | Latest |
| **Authentication** | [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/) | Latest |
| **Containerization** | [Docker](https://www.docker.com/) | Latest |
| **Orchestration** | [Docker Compose](https://docs.docker.com/compose/) | v2+ |

---

## Prerequisites

Before deploying this application, ensure you have the following installed on your server/machine:

- **Docker** (v24.x or higher)
- **Docker Compose** (v2.x or higher)
- **Git** (for cloning the repository)

---

## Deployment Guide

Follow these steps to deploy the Walet Backend application:

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd walet-main-service
```

### Step 2: Configure Environment Variables

Create a `.env` file in the root directory (or rely on the `docker-compose.yml` defaults for testing, but strictly NOT recommended for production).

Recommended `.env` content:

```env
DB_NAME=walet
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key-here
DEBUG=0
FRONTEND_URL=http://localhost:3000
EMAIL_URL=http://localhost:8025
SETTINGS_MODULE=walet.config.settings_prod
```

### Step 3: Build and Start the Application

Run the following command to build and start all services (App & Database):

```bash
docker compose up -d --build
```

**Explanation of flags:**
- `-d`: Run in detached mode (background)
- `--build`: Force rebuild of Docker images

### Step 4: Verify Deployment

Check that containers are running:

```bash
docker compose ps
```

**Expected output:**
```
NAME                    IMAGE                    STATUS         PORTS
walet-main-service-app  walet-main-service-app   Up             0.0.0.0:80->80/tcp
walet-main-service-db   postgres:15-alpine       Up             5432/tcp
```

### Step 5: Access the API

The API will be accessible at:
```
http://<YOUR_SERVER_IP>:80/api/
```
(Exact path depends on `urls.py` configuration)

---

## Project Architecture

The deployment uses a **multi-container architecture** orchestrated by Docker Compose:

```
┌─────────────────────────────────────────────────────────────┐
│                        Host Machine                          │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              Docker Compose Network                  │   │
│   │                                                      │   │
│   │   ┌─────────────┐         ┌───────────────────┐     │   │
│   │   │  PostgreSQL │         │   Django App      │     │   │
│   │   │     (DB)    │◀────────│   (Gunicorn)      │     │   │
│   │   │             │         │                   │     │   │
│   │   │  Port: 5432 │         │    Port: 80       │     │   │
│   │   │ (Internal)  │         │   (Exposed)       │     │   │
│   │   └─────────────┘         └───────────────────┘     │   │
│   │                                     ▲                │   │
│   │                                     │                │   │
│   └─────────────────────────────────────┼───────────────┘   │
│                                         │                    │
└─────────────────────────────────────────┼────────────────────┘
                                          │
                                     Internet /
                                   Frontend App
                                     (Port 80)
```

### Container Details

#### 1. `app` Container
- **Image:** Built from `Dockerfile` (Python 3.13-slim)
- **Purpose:** Runs the Django application using Gunicorn.
- **Port:** 80 (Exposed to host).
- **Dependencies:** Waits for `db` container to be healthy.

#### 2. `db` Container
- **Image:** `postgres:15-alpine`
- **Purpose:** Primary database for the application.
- **Volume:** `postgres_data` (Persists data across restarts).

---

## Configuration

The application is configured via environment variables passed to the containers.

| Variable | Description | Default (if any) |
|----------|-------------|------------------|
| `DB_NAME` | Database name | `walet` |
| `DB_USERNAME` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `DB_HOST` | Database host hostname | `db` |
| `DB_PORT` | Database port | `5432` |
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode (1=True, 0=False) | `1` |
| `FRONTEND_URL` | URL of the frontend app | - |
| `SETTINGS_MODULE`| Django settings module | `walet.config.settings_prod` |

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
- Ensure the `db` container is running (`docker compose ps`).
- Check logs: `docker compose logs app`.
- Verify `DB_HOST` is set to `db` (the service name in docker-compose).

#### 2. Port 80 Already in Use
- Cannot bind port 80? Change the mapping in `docker-compose.yml`:
  ```yaml
  ports:
    - "8080:80"  # Expose on port 8080 instead
  ```

#### 3. Static Files Not Loading
- In production, Gunicorn does not serve static files by default unless configured with WhiteNoise or Nginx. Ensure WhiteNoise is set up or use a reverse proxy.

### Useful Commands

```bash
# View logs
docker compose logs -f

# Run migrations manually (if needed)
docker compose exec app python manage.py migrate

# Create superuser
docker compose exec app python manage.py createsuperuser
```

---

## License

This project was created for educational purposes as part of a Cloud Computing course.
