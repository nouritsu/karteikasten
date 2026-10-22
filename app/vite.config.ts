/// <reference types="vitest/config" />
import { readFileSync } from 'node:fs'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

const { version } = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf8'))

// A plain static build: Capacitor serves it from the APK, deck included (D40, D41).
export default defineConfig({
  plugins: [svelte()],
  // Every study event records the app version that wrote it.
  define: { __APP_VERSION__: JSON.stringify(version) },
  test: {
    include: ['src/**/*.test.ts'],
  },
})
