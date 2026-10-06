/// <reference types="vitest/config" />
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Catppuccin Mocha's base, like the icon: the splash screen before the app paints.
const BACKGROUND = '#1e1e2e'

export default defineConfig({
  plugins: [
    svelte(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: false,
      manifest: {
        name: 'Karteikasten',
        short_name: 'Karteikasten',
        lang: 'de',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        background_color: BACKGROUND,
        theme_color: BACKGROUND,
        icons: [
          { src: '/generated/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/generated/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/generated/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // The app shell is precached; the deck is deployed separately and cached
        // as it is used: latest.json network-first, versioned files cache-first.
        globPatterns: ['**/*.{js,css,html,woff2,png,svg,webmanifest}'],
        globIgnores: ['deck/**'],
        navigateFallbackDenylist: [/^\/deck\//],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname === '/deck/latest.json',
            handler: 'NetworkFirst',
            options: { cacheName: 'deck-latest' },
          },
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/deck/'),
            handler: 'CacheFirst',
            options: { cacheName: 'deck', expiration: { maxEntries: 20000 } },
          },
        ],
      },
    }),
  ],
  test: {
    include: ['src/**/*.test.ts'],
  },
})
