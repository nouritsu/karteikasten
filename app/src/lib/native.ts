// The Android side (Native.java): the backup the regular exports copy, their run times,
// the study reminders and the cloud backup switch. In a browser every call is a no-op.

import { Capacitor, registerPlugin } from '@capacitor/core'

export interface ReminderItem {
  at: number // epoch ms
  title: string
  text: string
}

/** How the last regular export went, as Exports.java recorded it. */
export interface ExportResult {
  at: string // ISO time
  path?: string
  error?: string
}

interface NativePlugin {
  stage(options: { json: string }): Promise<void>
  planExports(options: { runs: number[]; oneFile: boolean }): Promise<void>
  lastExport(): Promise<{ result: string | null }>
  planReminders(options: { items: ReminderItem[] }): Promise<void>
  askNotifications(): Promise<{ allowed: boolean }>
  setCloudBackup(options: { on: boolean }): Promise<void>
}

const Plugin = registerPlugin<NativePlugin>('Native')
export const native = (): boolean => Capacitor.isNativePlatform()

/** Saves the backup the export alarm copies to Documents/Karteikasten/. */
export async function stage(json: string): Promise<void> {
  if (native()) await Plugin.stage({ json })
}

export async function planExports(runs: number[], oneFile: boolean): Promise<void> {
  if (native()) await Plugin.planExports({ runs, oneFile })
}

export async function lastExport(): Promise<ExportResult | null> {
  if (!native()) return null
  const { result } = await Plugin.lastExport()
  if (!result) return null
  try {
    const parsed = JSON.parse(result) as ExportResult
    return typeof parsed.at === 'string' ? parsed : null
  } catch {
    return null
  }
}

export async function planReminders(items: ReminderItem[]): Promise<void> {
  if (native()) await Plugin.planReminders({ items })
}

/** Whether reminders may be posted: true in a browser, where there are none. */
export async function askNotifications(): Promise<boolean> {
  if (!native()) return true
  return (await Plugin.askNotifications()).allowed
}

export async function setCloudBackup(on: boolean): Promise<void> {
  if (native()) await Plugin.setCloudBackup({ on })
}
