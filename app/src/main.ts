import { mount } from 'svelte'
import { registerSW } from 'virtual:pwa-register'
import './app.css'
import App from './App.svelte'
import { paintStatusBar } from './lib/theme'

registerSW({ immediate: true })
// index.html picked the theme; the app's status bar icons follow it.
paintStatusBar()

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
