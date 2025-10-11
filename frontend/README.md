# MenuMind AI Frontend 🥗🤖

React frontend for the MenuMind AI family food intelligence platform.

## Features

- 🛒 **Real-time Collaborative Shopping Lists** - Multi-user editing with WebSocket sync
- 🗄️ **Smart Archive Management** - Advanced deletion with ownership transfer
- 📱 **Responsive Design** - Optimized for desktop and mobile
- 🎨 **Modern UI** - Built with Tailwind CSS and React components
- 🔐 **JWT Authentication** - Secure user authentication and session management
- 📡 **Live Notifications** - Real-time updates via WebSocket connections

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **React Hot Toast** for notifications
- **WebSocket Client** for real-time features
- **React Context** for state management

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm start
```

3. Access the app:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Available Scripts

- `npm start` - Development server
- `npm run build` - Production build
- `npm test` - Run tests
- `npm run lint` - Lint code

## Project Structure

```
src/
├── components/          # Reusable UI components
├── contexts/           # React Context providers
├── pages/              # Page components
├── services/           # API and WebSocket services
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── hooks/              # Custom React hooks
```

## Key Components

- **CollaborationContext** - Real-time collaboration state management
- **AuthContext** - User authentication and session handling  
- **ShoppingList** - Main collaborative list interface
- **ArchivePage** - Archive management with ownership transfer
- **Navigation** - App navigation and user interface

## Real-time Features

- Live shopping list collaboration
- Instant participant updates
- Real-time item synchronization
- WebSocket connection management
- Automatic reconnection handling

## Build & Deploy

Production build:
```bash
npm run build
```

The build artifacts will be in the `build/` directory, ready for deployment.
