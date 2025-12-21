# HealthScan Mobile App 📱

React Native mobile app for HealthScan using Expo. Scan medical documents, check drug interactions, and get diet recommendations on the go.

## Features

- 📸 **Camera Capture** - Take photos of prescriptions and medical forms
- 🖼️ **Image Library** - Select images from your photo library
- 🔍 **Real-time Quality Check** - Get feedback on image quality before upload
- 💊 **Prescription Extraction** - Extract medication details instantly
- ⚠️ **Drug Interaction Checking** - Check for dangerous interactions
- 🥗 **Diet Recommendations** - Get personalized nutrition advice
- 🌐 **Cross-platform** - Works on iOS, Android, and Web

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Configuration

Create `.env` file in the `mobile/` directory:

```bash
EXPO_PUBLIC_API_URL=http://localhost:8000
```

For physical device testing, use your computer's IP address:
```bash
EXPO_PUBLIC_API_URL=http://192.168.1.XXX:8000
```

### 3. Run the App

```bash
# Start Expo development server
npm start

# Or run directly on device:
npm run ios      # iOS Simulator
npm run android  # Android Emulator
npm run web      # Web browser (for testing)
```

### 4. Test on Physical Device

1. Install **Expo Go** app on your phone:
   - [iOS App Store](https://apps.apple.com/app/expo-go/id982107779)
   - [Google Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)

2. Scan the QR code shown in terminal/browser

3. Make sure your phone and computer are on the same WiFi network

## API Endpoints Used

The mobile app connects to the same FastAPI backend as the web app:

- `POST /extract-prescription` - Fast prescription extraction
- `POST /analyze-and-execute` - Full pipeline (vision + planning + execution)
- `POST /check-prescription-interactions` - Drug interaction checking
- `POST /get-diet-recommendations` - Diet recommendations

## Testing Notes

### iOS Simulator
- ❌ Camera won't work - use image picker instead
- ✅ Image library works
- ✅ All other features work

### Android Emulator
- ✅ Camera works if permissions granted
- ✅ Image library works
- ✅ All features work

### Physical Device (Recommended)
- ✅ Camera works perfectly
- ✅ Image library works
- ✅ Best testing experience
- ⚠️ Make sure backend is accessible from device (use IP address, not localhost)

## Troubleshooting

### "Network Error" or "Failed to fetch"
- Make sure backend is running: `cd backend && uvicorn api.main:app --reload`
- Check `EXPO_PUBLIC_API_URL` is correct
- For physical device: Use your computer's IP address, not `localhost`
- Check firewall settings

### Camera Permission Denied
- iOS: Go to Settings → HealthScan → Camera → Allow
- Android: App will prompt automatically

### Image Quality Warnings
- The app checks image quality before upload
- If you see warnings, try:
  - Better lighting
  - Hold camera steady
  - Get closer to document
  - Avoid glare and shadows

## Project Structure

```
mobile/
├── App.tsx              # Main app component
├── screens/
│   └── ScanScreen.tsx   # Main scan interface
├── lib/
│   ├── api.ts           # API client
│   └── imageQuality.ts  # Image quality checking
└── assets/              # App icons and images
```

## Development

### Adding New Features

1. Create new screen in `screens/`
2. Add API function in `lib/api.ts`
3. Update navigation in `App.tsx`

### Building for Production

```bash
# iOS
eas build --platform ios

# Android
eas build --platform android
```

Requires Expo EAS account and configuration.

## Dependencies

- `expo` - Expo SDK
- `expo-camera` - Camera access
- `expo-image-picker` - Image selection
- `expo-file-system` - File operations
- `axios` - HTTP client
- `react-native` - React Native framework

## License

MIT - See root LICENSE file
