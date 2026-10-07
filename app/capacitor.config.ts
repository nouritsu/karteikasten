import type { CapacitorConfig } from '@capacitor/cli'

// The Android app (D40): the Vite build in a WebView, served from https://localhost/
// with the deck under /deck/ (D41). nix/apk.nix copies both in before Gradle runs.
const config: CapacitorConfig = {
  appId: 'com.nouritsu.karteikasten',
  appName: 'Karteikasten',
  webDir: 'dist',
  // Catppuccin Mocha's base, behind the WebView until the page paints.
  backgroundColor: '#1e1e2e',
  plugins: {
    // The page draws under the status and navigation bars and pads itself by
    // --safe-area-inset-*; src/lib/theme.ts sets the bars' icon colour.
    SystemBars: { insetsHandling: 'css' },
  },
}

export default config
