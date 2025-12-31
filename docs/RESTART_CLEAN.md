# How to Restart The Grey Tutor with Clean Cache

## Quick Steps

1. **Stop all services:**
   - Press `Ctrl+C` in the terminal running `start_all.ps1`
   - Wait for Docker containers to stop

2. **Clear Metro bundler cache:**
   ```powershell
   # From the project root
   npx expo start --clear
   # Then immediately press Ctrl+C to stop it
   ```

   OR manually delete cache:
   ```powershell
   # Clear Expo cache
   rm -r -Force node_modules/.cache
   rm -r -Force .expo

   # Clear frontend cache if it exists
   cd thegreytutor/frontend
   rm -r -Force node_modules/.cache
   rm -r -Force .expo
   cd ../..
   ```

3. **Clear React Native packager cache:**
   ```powershell
   npx react-native start --reset-cache
   # Then immediately press Ctrl+C to stop it
   ```

4. **Restart all services:**
   ```powershell
   .\start_all.ps1
   ```

5. **In the Expo terminal that opens:**
   - Press `r` to reload the app
   - Or press `Shift+r` to reload and clear cache
   - Or scan the QR code again to restart the app on your device

## If Changes Still Don't Appear

### Option 1: Clear Watchman Cache (if installed)
```powershell
watchman watch-del-all
```

### Option 2: Reinstall Dependencies
```powershell
# Stop services first
# Then:
rm -r -Force node_modules
npm install

cd thegreytutor/frontend
rm -r -Force node_modules
npm install
cd ../..

# Restart
.\start_all.ps1
```

### Option 3: Hard Reset Expo
```powershell
# From project root
npx expo start -c
```

### Option 4: Rebuild the App
If you're using Expo Go:
- Close the Expo Go app completely
- Restart it
- Scan QR code again

If you're using a development build:
- Rebuild the app: `npx expo run:android` or `npx expo run:ios`

## Verifying New Code Is Loaded

1. **Check for MapTab:**
   - Open the app
   - Look at the bottom tab bar
   - You should see 4 tabs: "The Grey Tutor", "Learning Paths", "Journey Map", "Profile"

2. **Open Journey Map:**
   - Tap on "Journey Map" tab (map icon)
   - You should see:
     - Header with Knowledge Points, Regions Unlocked, Completed count
     - Middle Earth map with parchment background
     - Region markers (circular dots)
     - Legend at bottom right

3. **Check Console:**
   - In the Expo terminal, watch for:
     - No red errors
     - Log message: "Fetching journey state for user..."
     - API calls to `/api/journey/state`

## Common Issues

**Issue:** "Module not found" errors
**Solution:**
```powershell
npm install
cd thegreytutor/frontend && npm install && cd ../..
```

**Issue:** TypeScript errors
**Solution:**
```powershell
cd thegreytutor/frontend
npm run type-check
```

**Issue:** Can't connect to backend
**Solution:**
- Check backend is running on http://localhost:8000
- Check Docker containers: `docker ps`
- Restart: `docker-compose down && docker-compose up -d`

**Issue:** White screen / blank screen
**Solution:**
- Check Expo terminal for errors
- Press `Shift+r` in Expo terminal to fully reload
- Check backend logs for API errors
