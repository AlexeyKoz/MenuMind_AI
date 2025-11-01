# Data Directory

This directory contains database files used by the application:

- `iml.db` - Ingredient Master List (10,000+ ingredients in EN/RU/HE)
- `cooklingo.db` - CookLingo cooking terms glossary (500+ terms)

These files are used for fast in-memory caching via the service layer.

## Docker

In Docker containers, these files are mounted as volumes:
```yaml
volumes:
  - ./backend/data:/app/data
```

## Environment Variables

You can override the paths using:
```bash
IML_DB_PATH=/custom/path/iml.db
COOKLINGO_DB_PATH=/custom/path/cooklingo.db
```

