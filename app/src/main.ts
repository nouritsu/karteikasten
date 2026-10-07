import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'
import { paintStatusBar } from './lib/theme'

// index.html picked the theme; the app's status bar icons follow it.
paintStatusBar()

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
