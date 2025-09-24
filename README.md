# MenuMind AI 🥗🤖

A complete family food intelligence platform combining shopping coordination, meal planning, inventory management, and personalized nutrition coaching using advanced AI.

## Features

### 🛒 Smart Collaborative Shopping Lists
- **Real-time Collaboration** - Multiple users can edit lists simultaneously with instant WebSocket updates
- **Advanced Permission System** - Granular control over who can edit, add items, or invite others
- **Collaboration Keys** - Share lists securely using unique collaboration keys
- **Live Participant Management** - See who's online and editing in real-time
- **AI-Powered Item Suggestions** - Smart item recommendations based on context

### 🗄️ Advanced Archive & Deletion System
- **Smart Archive Management** - Soft delete lists with 5-second cancellation timer
- **Automatic Ownership Transfer** - When creators permanently delete lists, ownership automatically transfers to the oldest participant
- **Intelligent Selection Algorithm** - New owners selected based on join date, activity level, and alphabetical order
- **Participant Protection** - Collaborators can remove lists from their view without affecting others
- **Auto-Cleanup System** - Archived lists automatically cleaned up after 60 days with transfer notifications

### 🤝 Real-time Collaboration Features
- **Live Item Updates** - See items being added, edited, and checked off in real-time
- **Participant Notifications** - Get notified when users join, leave, or when ownership changes
- **Typing Indicators** - See when other users are actively editing
- **Permission Management** - Update collaborator permissions on-the-fly
- **Connection Status** - Visual indicators showing real-time connection status

### 🎯 Additional Features
- 🍳 **AI Recipe Generation** - Create recipes based on available ingredients and nutrition goals
- 📊 **Nutrition Tracking** - AI-powered meal analysis and macro tracking
- 💑 **Partner Sync** - Couples can share lists and coordinate nutrition goals
- 🏪 **Store Integration** - Mock integrations with Israeli stores (Wolt, Shufersal)
- 🤖 **AI Coaching** - Personalized nutrition coaching and insights

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
- API Testing: http://localhost:8000/test_backend.html

### Default Credentials
- Username: `testuser1` / Password: `password123`
- Username: `testuser2` / Password: `password123`

## Key Collaboration Workflows

### 🤝 Creating & Sharing Lists
1. **Create List** - Any user can create a new collaborative shopping list
2. **Share Key** - Creator shares the unique collaboration key (visible in sidebar)
3. **Join List** - Collaborators enter the key to join the list instantly
4. **Set Permissions** - Creator manages who can edit, add items, or invite others

### 🗂️ Archive & Ownership Management
1. **Archive List** - Creator deletes list → moves to archive (5-sec cancellation)
2. **Smart Transfer** - Permanent deletion → ownership auto-transfers to oldest participant
3. **Participant Protection** - Non-creators can remove lists from their view
4. **Auto-Cleanup** - 60+ day old archives trigger ownership transfer or deletion

### 📱 Real-time Collaboration
- **Live Updates** - All changes sync instantly across all connected users
- **Participant Awareness** - See who's online and editing
- **Smart Notifications** - Get notified about joins, leaves, ownership changes
- **Permission Control** - Update collaborator access levels on-the-fly

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
POST /api/users/auth/login/
POST /api/users/auth/register/
GET /api/users/profile/
```

### Shopping Lists
```bash
GET/POST /api/shopping/lists/                    # List & create shopping lists
GET /api/shopping/lists/{id}/                    # Get specific list details
DELETE /api/shopping/lists/{id}/                 # Archive list (soft delete)
POST /api/shopping/lists/{id}/restore/           # Restore archived list
DELETE /api/shopping/lists/{id}/permanent-delete/ # Permanently delete from archive
POST /api/shopping/lists/{id}/add_item/          # Add item to list
POST /api/shopping/lists/{id}/ai_add_items/      # AI-powered bulk item addition
```

### Collaboration
```bash
POST /api/shopping/lists/{id}/add_collaborator/  # Add collaborator by key
POST /api/shopping/lists/{id}/leave/             # Leave collaborative list
PATCH /api/shopping/lists/{id}/collaborators/{user_id}/ # Update permissions
GET /api/shopping/lists/{id}/collaborators/      # List collaborators
```

### Archive Management
```bash
GET /api/shopping/lists/archived/                # List archived lists
POST /api/shopping/lists/{id}/restore/           # Restore from archive
DELETE /api/shopping/lists/{id}/permanent-delete/ # Permanent deletion
```

### Items
```bash
POST /api/shopping/items/{id}/toggle_complete/   # Toggle item completion
PATCH /api/shopping/items/{id}/update_weight/    # Update weight quantity
PATCH /api/shopping/items/{id}/update_liquid/    # Update liquid quantity
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

### Real-time Collaboration
```bash
ws://localhost:8000/ws/shopping/{list_id}/       # Real-time shopping list collaboration
ws://localhost:8000/ws/user-notifications/      # Personal user notifications
```

**Shopping List Events:**
- `item_added` - Item added to list
- `item_updated` - Item modified (completion, quantities)
- `item_deleted` - Item removed from list
- `collaborator_added` - New collaborator joined
- `collaborator_updated` - Permissions changed
- `list_deleted` - List archived by creator

**User Notification Events:**
- `list_access_granted` - Added as collaborator to a list
- `participant_left` - Someone left your list
- `list_permanently_deleted` - List permanently deleted
- `ownership_transferred` - List ownership transferred to you
- `deletion_warning` - List will be auto-deleted soon

### Additional WebSockets
- Nutrition Coach: `ws://localhost:8000/ws/nutrition/`

## Testing

### Automated Tests
Run tests:
```bash
make test
```

### Backend API Testing
Interactive API testing and status monitoring available at:
```
http://localhost:8000/test_backend.html
```
This comprehensive testing page provides real-time API testing, authentication management, and server status monitoring for all backend endpoints.

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
