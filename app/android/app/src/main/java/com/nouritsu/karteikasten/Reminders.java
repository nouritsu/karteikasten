package com.nouritsu.karteikasten;

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * The study reminder (D63). The web app plans the next week's reminders whenever it goes
 * to the background, each with its time and its text, counted as the status bar would show
 * them then (src/lib/reminder.ts); a day with nothing due, or one already studied, has
 * none. An alarm posts each one and sets the next, with the app closed too.
 */
final class Reminders {

    static final String CHANNEL = "reminder";
    private static final int ID = 1;

    private Reminders() {}

    /** Sets the alarm for the next planned reminder after now, or none. */
    static void schedule(Context context) {
        AlarmReceiver.cancel(context, intent(context));
        JSONObject next = next(Native.prefs(context), System.currentTimeMillis());
        if (next != null) AlarmReceiver.setAlarm(context, next.optLong("at"), intent(context));
    }

    /** Posts the reminder that is due now, if any, and sets the next. */
    static void fire(Context context) {
        long now = System.currentTimeMillis();
        SharedPreferences prefs = Native.prefs(context);
        // A reminder whose time passed with the phone off is a minute or so late at most;
        // one more than an hour late is stale.
        JSONObject due = latest(prefs, now);
        if (due != null && now - due.optLong("at") < 60 * 60 * 1000) post(context, due.optString("title"), due.optString("text"));
        schedule(context);
    }

    static void post(Context context, String title, String text) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return;
        channel(context);
        Intent open = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName());
        PendingIntent tap = PendingIntent.getActivity(context, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        NotificationCompat.Builder notification = new NotificationCompat.Builder(context, CHANNEL)
                .setSmallIcon(R.drawable.ic_stat_study)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(text))
                .setContentIntent(tap)
                .setAutoCancel(true)
                .setCategory(NotificationCompat.CATEGORY_REMINDER);
        NotificationManagerCompat.from(context).notify(ID, notification.build());
    }

    /** Takes a posted reminder away: the app was opened, so it has done its job. */
    static void clear(Context context) {
        NotificationManagerCompat.from(context).cancel(ID);
    }

    private static void channel(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager manager = context.getSystemService(NotificationManager.class);
        if (manager.getNotificationChannel(CHANNEL) != null) return;
        manager.createNotificationChannel(new NotificationChannel(CHANNEL, "Study reminder", NotificationManager.IMPORTANCE_DEFAULT));
    }

    private static JSONArray planned(SharedPreferences prefs) {
        try {
            return new JSONArray(prefs.getString("reminders", "[]"));
        } catch (Exception e) {
            return new JSONArray();
        }
    }

    /** The first planned reminder after `now`. */
    private static JSONObject next(SharedPreferences prefs, long now) {
        JSONArray list = planned(prefs);
        for (int i = 0; i < list.length(); i++) {
            JSONObject item = list.optJSONObject(i);
            if (item != null && item.optLong("at") > now) return item;
        }
        return null;
    }

    /** The last planned reminder at or before `now`. */
    private static JSONObject latest(SharedPreferences prefs, long now) {
        JSONArray list = planned(prefs);
        JSONObject found = null;
        for (int i = 0; i < list.length(); i++) {
            JSONObject item = list.optJSONObject(i);
            if (item != null && item.optLong("at") <= now) found = item;
        }
        return found;
    }

    private static PendingIntent intent(Context context) {
        Intent intent = new Intent(context, AlarmReceiver.class).setAction(AlarmReceiver.REMIND);
        return PendingIntent.getBroadcast(context, 2, intent, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }
}
