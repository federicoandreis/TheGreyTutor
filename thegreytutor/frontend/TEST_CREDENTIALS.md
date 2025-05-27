# The Grey Tutor - Test Credentials

## 🔐 Login Credentials for Testing

### Test User Account
- **Email**: `test@example.com`
- **Password**: `password123` (any password works in mock mode)
- **Display Name**: Test User
- **Level**: 2
- **Experience**: 450 XP

### Gandalf Account (Advanced User)
- **Email**: `gandalf@middleearth.com`
- **Password**: `any_password` (any password works in mock mode)
- **Display Name**: Gandalf the Grey
- **Level**: 8
- **Experience**: 2340 XP

## 📱 How to Test

### Web Browser
1. Open http://localhost:8083 in your browser
2. Use any of the credentials above
3. Any password will work since we're using mock authentication

### Mobile Device (Expo Go)
1. Make sure your phone and computer are on the same WiFi network
2. Download Expo Go app from App Store/Google Play
3. Scan the QR code from the terminal
4. If QR code doesn't work, try the tunnel option (see below)

## 🔧 Expo Go Troubleshooting

If you can't connect with Expo Go:

### Option 1: Use Tunnel Mode
```bash
cd thegreytutor/frontend
npx expo start --tunnel
```

### Option 2: Check Network
- Ensure phone and computer are on same WiFi
- Disable VPN if active
- Check firewall settings

### Option 3: Use Development Build
```bash
cd thegreytutor/frontend
npx expo start --dev-client
```

## ✅ What's Working
- ✅ All assets created (icons, splash screens)
- ✅ Redux store with mock database
- ✅ Authentication system
- ✅ Beautiful UI with Middle Earth theme
- ✅ Web version fully functional
- ✅ No RCTFatal errors
- ✅ TypeScript compilation successful

## 🎯 Features to Test
1. **Login** - Use test credentials above
2. **Registration** - Create new account
3. **Chat Interface** - Talk with Gandalf
4. **Navigation** - Switch between screens
5. **Redux State** - All data persists properly
