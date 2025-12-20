# SCANX Mobile App

React Native mobile app for SCANX using Expo.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set environment variable:
Create `.env` file:
```
EXPO_PUBLIC_API_URL=http://localhost:8000
```

3. Run the app:
```bash
# iOS
npm run ios

# Android
npm run android

# Web (for testing)
npm run web
```

## Features

- Camera capture for scanning interfaces
- Image library picker
- Intent input
- Results display
- Connects to same FastAPI backend as web app

## Notes

- Make sure backend is running before testing
- For iOS simulator, camera won't work - use image picker instead
- For Android emulator, camera should work if permissions are granted

