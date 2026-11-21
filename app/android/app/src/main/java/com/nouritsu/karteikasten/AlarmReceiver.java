package com.nouritsu.karteikasten;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

/**
 * The app's alarms and the system events that move them: a regular export (Exports), a
 * study reminder (Reminders), and a reboot, an app update or a clock change, which drop or
 * shift them.
 */
public class AlarmReceiver extends BroadcastReceiver {

    static final String EXPORT = "com.nouritsu.karteikasten.RUN_EXPORT";
    static final String REMIND = "com.nouritsu.karteikasten.REMIND";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (EXPORT.equals(action)) {
            Exports.run(context);
        } else if (REMIND.equals(action)) {
            Reminders.fire(context);
        } else {
            Exports.schedule(context);
            Reminders.schedule(context);
        }
    }

    /** Sets `alarm` for `at`: exact when Android allows it, else as close as its batching makes it. */
    static void setAlarm(Context context, long at, PendingIntent alarm) {
        AlarmManager alarms = context.getSystemService(AlarmManager.class);
        boolean exact = Build.VERSION.SDK_INT < Build.VERSION_CODES.S || alarms.canScheduleExactAlarms();
        if (exact) alarms.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, alarm);
        else alarms.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, alarm);
    }

    static void cancel(Context context, PendingIntent alarm) {
        context.getSystemService(AlarmManager.class).cancel(alarm);
    }
}
