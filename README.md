# MenuMind AI 🥗🤖

A complete family food intelligence platform combining shopping coordination, meal planning, inventory management, and personalized nutrition coaching using advanced AI.

## Features

- 🛒 **Smart Shopping Lists** - Real-time collaborative shopping with AI-powered item suggestions
- 🍳 **AI Recipe Generation** - Create recipes based on available ingredients and nutrition goals
- 📊 **Nutrition Tracking** - AI-powered meal analysis and macro tracking
- 💑 **Partner Sync** - Couples can share lists and coordinate nutrition goals
- 🏪 **Store Integration** - Mock integrations with Israeli stores (Wolt, Shufersal)
- 🤖 **AI Coaching** - Personalized nutrition coaching and insights
- 📱 **Real-time Updates** - WebSocket-powered instant synchronization

## Tech Stack

### Backend
- Django 4.2 with Django Channels
- PostgreSQL 15
- Redis 7
- OpenAI GPT-4 with LangChain
- WebSockets for real-time features

### Frontend
- React 18 with TypeScript
- Tailwind CSS for styling
- Recharts for data visualization
- WebSocket client for real-time updates

### Infrastructure
- Docker & Docker Compose
- Nginx reverse proxy
- GitHub Actions CI/CD
- Production-ready deployment

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/menumine-ai.git
cd menumine-ai
```

2. Copy environment file:
```bash
cp .env.development.example .env
```

3. Add your OpenAI API key to `.env`:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

4. Start development environment:
```bash
make dev
# or
docker-compose up
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin: http://localhost:8000/admin

### Default Credentials
- Username: `testuser1`
- Password: `password123`

## Production Deployment

1. Copy and configure production environment:
```bash
cp .env.production.example .env.production
# Edit .env.production with your production values
```

2. Deploy:
```bash
./scripts/deploy.sh
# or
make prod
```

## API Documentation

### Authentication
```bash
POST /api/auth/login/
POST /api/auth/register/
POST /api/auth/profile/
```

### Shopping
```bash
GET/POST /api/shopping/lists/
POST /api/shopping/lists/{id}/add_item/
POST /api/shopping/lists/{id}/ai_add_items/
POST /api/shopping/items/{id}/toggle_complete/
```

### Nutrition
```bash
GET /api/nutrition/entries/today_summary/
POST /api/nutrition/entries/ai_log_meal/
GET /api/nutrition/entries/weekly_report/
POST /api/nutrition/entries/get_coaching/
```

### AI Services
```bash
POST /api/ai/assistant/
POST /api/ai/recipes/
POST /api/ai/coaching/
```

## WebSocket Endpoints
- Shopping List Sync: `ws://localhost:8000/ws/shopping/{list_id}/`
- Nutrition Coach: `ws://localhost:8000/ws/nutrition/`

## Testing
Run tests:
```bash
make test
```

## Backup & Restore
Backup database:
```bash
make backup
```

Restore from backup:
```bash
make restore
```

## Available Commands

```bash
make dev      # Start development environment
make prod     # Start production environment
make build    # Build all Docker images
make test     # Run tests
make clean    # Clean up containers and volumes
make logs     # Show logs
make shell    # Open Django shell
make migrate  # Run database migrations
make seed     # Seed database with initial data
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License.

## Support
For support, email support@menumine-ai.com or open an issue.
