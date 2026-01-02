# Development Guide

## Quick Start

### First Time Setup
```powershell
# Install dependencies
npm install
cd thegreytutor/frontend && npm install && cd ../..
cd thegreytutor/backend && pip install -r requirements.txt && cd ../..

# Start all services
.\start_all.ps1
```

### Daily Development

**Start everything (recommended):**
```powershell
.\start_all.ps1
```
This clears cache automatically so you'll always see your latest changes.

**Fast start (when you haven't changed code):**
```powershell
.\start_all.ps1 -fast
```
Skips cache clearing for faster startup (~30 seconds faster).

**Stop everything:**
```powershell
.\stop_all.ps1
```
Or press `Ctrl+C` in the start_all.ps1 window.

## What the Script Does

### start_all.ps1

1. **Starts Docker containers** (Neo4j, PostgreSQL, Redis)
2. **Starts backend** (FastAPI on http://localhost:8000)
3. **Clears Metro cache** (unless `-fast` flag used)
4. **Starts Expo** from `thegreytutor/frontend/` with `--clear` flag

### Why Clear Cache by Default?

During development, **cache issues are the #1 cause of "changes not appearing"**:

- ✅ Metro bundler caches compiled JavaScript
- ✅ Expo caches app bundles
- ✅ React Native caches components
- ✅ Node caches modules

**Clearing cache ensures:**
- New components always load
- Navigation changes take effect
- TypeScript changes compile fresh
- Redux store updates work
- API client changes apply

**Time cost:** Only ~10-15 seconds extra on startup
**Benefit:** Zero frustration from stale cache

### When to Use Fast Mode

Use `.\start_all.ps1 -fast` when:
- You're just fixing a typo or comment
- You only changed backend code
- You're testing the same code multiple times
- You need to restart quickly

## Project Structure

```
thegreytutor/
├── start_all.ps1              # Main startup script (ALWAYS USE THIS)
├── stop_all.ps1               # Stop all services
├── docker-compose.yml         # Docker services config
│
├── thegreytutor/
│   ├── backend/               # FastAPI backend
│   │   ├── src/
│   │   │   ├── main.py       # FastAPI app entry
│   │   │   ├── api/          # API routes
│   │   │   └── agents/       # AI agents (Journey, Quiz, etc.)
│   │   └── tests/
│   │
│   └── frontend/              # React Native app (THIS IS WHERE EXPO RUNS)
│       ├── app.json           # Expo config
│       ├── App.tsx            # App entry point
│       ├── src/
│       │   ├── screens/       # Screen components
│       │   ├── components/    # Reusable components
│       │   ├── navigation/    # Navigation config
│       │   ├── services/      # API clients
│       │   └── store/         # State management
│       └── __tests__/
│
└── package.json               # ROOT package.json (LEGACY - DO NOT USE)
```

## Why Expo Runs from thegreytutor/frontend/

The **correct** Expo project is in `thegreytutor/frontend/`:
- ✅ Has `app.json` with proper config
- ✅ Has `App.tsx` entry point
- ✅ Has all source code in `src/`
- ✅ Has proper dependencies in `package.json`

The root `package.json` is **leftover configuration** and should be ignored.

**Old (incorrect) way:**
```powershell
# DON'T DO THIS - runs from wrong directory
npx expo start  # from root
```

**New (correct) way:**
```powershell
# Script does this automatically
cd thegreytutor/frontend
npx expo start --clear
```

## Common Development Tasks

### See Your Latest Code Changes

**Option 1: Restart with cache clear (recommended)**
```powershell
# In terminal running start_all.ps1, press Ctrl+C
.\start_all.ps1
```

**Option 2: Reload in Expo (faster, if cache isn't the issue)**
In the Expo terminal window:
- Press `r` - Regular reload
- Press `Shift+r` - Reload and clear app cache
- Press `c` - Clear Metro bundler cache

### Check What's Running

```powershell
# Check Docker containers
docker ps

# Check processes
Get-Process | Where-Object {$_.ProcessName -like "*node*" -or $_.ProcessName -like "*python*"}
```

### View Logs

**Backend logs:**
- Look at the backend PowerShell window
- Or visit http://localhost:8000/docs

**Frontend logs:**
- Look at the Expo PowerShell window
- Or check your device/emulator console

**Database logs:**
```powershell
docker logs thegreytutor-neo4j-1
docker logs thegreytutor-postgres-1
docker logs thegreytutor-redis-1
```

### Run Tests

**Backend tests:**
```powershell
cd thegreytutor/backend
pytest
pytest tests/agents/test_journey_agent.py  # Specific test file
cd ../..
```

**Frontend tests:**
```powershell
cd thegreytutor/frontend
npm test
npm test -- RegionMarker  # Specific test
cd ../..
```

### Type Checking

```powershell
cd thegreytutor/frontend
npm run type-check
cd ../..
```

### Linting

```powershell
cd thegreytutor/frontend
npm run lint
cd ../..
```

## Troubleshooting

### Changes Don't Appear in App

1. **Restart with cache clear:**
   ```powershell
   # Stop services (Ctrl+C)
   .\start_all.ps1
   ```

2. **Force reload in Expo:**
   Press `Shift+r` in Expo terminal

3. **Check you're on the right branch:**
   ```powershell
   git branch
   git status
   ```

### "Module not found" Errors

```powershell
# Reinstall dependencies
cd thegreytutor/frontend
rm -r -Force node_modules
npm install
cd ../..

# Restart
.\start_all.ps1
```

### Backend API Not Responding

```powershell
# Check backend is running
curl http://localhost:8000/health

# Restart Docker
docker-compose down
docker-compose up -d

# Check logs
docker logs thegreytutor-postgres-1
```

### Port Already in Use

```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual number)
taskkill /PID <PID> /F

# Or use different port
# Edit start_all.ps1, change --port 8000 to --port 8001
```

### Expo Won't Start

```powershell
# Clear Expo cache manually
cd thegreytutor/frontend
rm -r -Force .expo
rm -r -Force node_modules/.cache
npx expo start --clear
cd ../..
```

### Docker Containers Won't Start

```powershell
# Stop all containers
docker-compose down

# Remove volumes (WARNING: deletes database data)
docker-compose down -v

# Restart
docker-compose up -d
```

## Performance Tips

### Speed Up Development

1. **Use fast mode when appropriate:**
   ```powershell
   .\start_all.ps1 -fast
   ```

2. **Keep services running:**
   - Don't restart unless you need to
   - Use `Shift+r` in Expo instead

3. **Use TypeScript check before committing:**
   ```powershell
   cd thegreytutor/frontend && npm run type-check && cd ../..
   ```

4. **Run tests in watch mode:**
   ```powershell
   cd thegreytutor/frontend && npm test -- --watch && cd ../..
   ```

### When to Do Full Restart

Full restart needed when:
- ✅ New npm packages installed
- ✅ Navigation structure changed
- ✅ New screens/components added
- ✅ API client changes
- ✅ Store/state management changes
- ❌ NOT needed for simple component edits
- ❌ NOT needed for style changes
- ❌ NOT needed for text changes

## Git Workflow

```powershell
# Create feature branch
git checkout -b feature-name

# Make changes...

# Test before committing
.\start_all.ps1
# Test in app

# Type check
cd thegreytutor/frontend && npm run type-check && cd ../..

# Run tests
cd thegreytutor/backend && pytest && cd ../..
cd thegreytutor/frontend && npm test && cd ../..

# Commit
git add .
git commit -m "feat: description of changes"

# Push
git push origin feature-name
```

## Environment Variables

### Frontend Setup

Copy the example environment file and configure as needed:
```powershell
cd thegreytutor/frontend
cp .env.example .env
```

**For mobile device testing via Expo Go:**

Edit `.env` to use your computer's local IP address:
```env
# Find your IP: ipconfig | findstr "IPv4" (Windows)
EXPO_PUBLIC_API_URL=http://YOUR_LOCAL_IP:8000
```

> **Note:** Your phone and computer must be on the same WiFi network for mobile testing.

### Backend Setup

Create `.env` in the project root if needed:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/thegreytutor
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
```

## Additional Resources

- **Journey Integration:** See [JOURNEY_INTEGRATION_GUIDE.md](JOURNEY_INTEGRATION_GUIDE.md)
- **API Documentation:** http://localhost:8000/docs
- **Neo4j Browser:** http://localhost:7474
- **Expo Documentation:** https://docs.expo.dev/
- **React Navigation:** https://reactnavigation.org/
