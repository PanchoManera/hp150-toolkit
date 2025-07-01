#!/bin/bash

# Fix macOS Bundle Script
# This script fixes common issues with macOS app bundles that show "damaged" errors

APP_NAME="HP150-Toolkit.app"

echo "🔧 Fixing macOS bundle permissions and signatures for $APP_NAME"

# Check if the app exists
if [ ! -d "$APP_NAME" ]; then
    echo "❌ Error: $APP_NAME not found in current directory"
    echo "   Please run this script in the same directory as the app"
    exit 1
fi

echo "📁 Found $APP_NAME"

# Remove quarantine attributes
echo "🧹 Removing quarantine attributes..."
sudo xattr -rd com.apple.quarantine "$APP_NAME" 2>/dev/null || true
xattr -cr "$APP_NAME" 2>/dev/null || true

# Fix permissions
echo "🔒 Setting correct permissions..."
sudo chmod +x "$APP_NAME/Contents/MacOS/HP150-Toolkit" 2>/dev/null || true
find "$APP_NAME" -type f -name "*.dylib" -exec chmod 755 {} \; 2>/dev/null || true
find "$APP_NAME" -type f -name "*.so" -exec chmod 755 {} \; 2>/dev/null || true

# Self-sign the bundle
echo "✍️  Self-signing the bundle..."
codesign --force --deep --sign - "$APP_NAME" 2>/dev/null || {
    echo "⚠️  Warning: Could not self-sign the bundle"
    echo "   The app might still work, but you may see security warnings"
}

# Verify signature
echo "🔍 Verifying bundle signature..."
if codesign --verify --deep "$APP_NAME" 2>/dev/null; then
    echo "✅ Bundle signature verified successfully"
else
    echo "⚠️  Bundle signature verification failed, but this might still work"
fi

# Final check
if [ -f "$APP_NAME/Contents/MacOS/HP150-Toolkit" ]; then
    echo "✅ Main executable found and accessible"
else
    echo "❌ Main executable not found or not accessible"
    exit 1
fi

echo ""
echo "🎉 Bundle fix completed!"
echo ""
echo "Try opening $APP_NAME now:"
echo "  • Double-click the app in Finder"
echo "  • Or run: open '$APP_NAME'"
echo ""
echo "If you still get security warnings:"
echo "  1. Go to System Preferences > Security & Privacy"
echo "  2. Look for a message about $APP_NAME being blocked"
echo "  3. Click 'Open Anyway'"
echo ""
