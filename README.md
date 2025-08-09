# Task Manager API - MacV AI

Lightweight Task Management System API built with FastAPI, SQLAlchemy, Celery, Redis, and Docker.

---

## Features

- User registration & login with JWT authentication
- Projects and Tasks CRUD
- Task filtering, sorting, pagination
- Assign tasks to users
- Background email notifications via Celery
- Daily summary email for overdue tasks
- Dockerized with Redis and FastAPI containers

---

## Requirements

- Docker & Docker Compose installed
- SMTP email credentials (for real email notifications)
- Python 3.11+ (for local dev, optional if using Docker)

---

## Setup Instructions

1. **Clone the repo:**

```bash
git clone https://github.com/yourusername/task-manager-api.git
cd task-manager
