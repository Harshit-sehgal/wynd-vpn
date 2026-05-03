# WYND VPN - Android Quick Start

## Requirements
- Android Studio (to build the APK)
- Android device (Android 7.0+ recommended)

## Build the APK

1. **Open in Android Studio**
   ```
   Open: clients/android/
   ```

2. **Build the APK**
   - Go to: Build → Build Bundle(s) / APK(s) → Build APK(s)
   - Or press: Ctrl+F9

3. **Transfer to phone**
   - Find APK at: `app/build/outputs/apk/debug/app-debug.apk`
   - Send to your Android device

## Install

1. Enable "Install from unknown sources" in Android settings
2. Open the APK file on your phone
3. Tap Install

## Connect

1. Open "WYND VPN" app
2. Tap "Connect"
3. Grant VPN permission when prompted

## How It Works

- Uses Android's built-in VpnService API
- Creates a virtual network interface
- Routes all app traffic through port 53 to WYND server
- Server forwards to the internet

## Server

- **IP:** 161.118.177.7
- **Port:** 53

(Already configured in the code)

## Troubleshooting

- **Connection fails?** Check your internet connection
- **App force closes?** Ensure you have VPN permission

## Disconnect

Tap "Disconnect" in the app to stop the VPN.