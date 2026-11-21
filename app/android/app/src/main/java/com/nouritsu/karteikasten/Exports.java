package com.nouritsu.karteikasten;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Environment;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Regular exports (D62). The study events live in the WebView's IndexedDB, which this side
 * cannot read, so the web app saves a backup to the app's own storage whenever it goes to
 * the background (src/lib/native.ts stage()); the events only change while the app runs, so
 * that copy is always current. At each run time the app planned, this copies it to
 * Documents/Karteikasten/, records how it went, and sets an alarm for the next run. It
 * makes a file a day, or with Keep one file one file that each run replaces.
 */
final class Exports {

    static final String FOLDER = "Karteikasten";
    static final String STAGED = "backup.json";

    private Exports() {}

    /** Sets the alarm for the next planned run after now, or none. */
    static void schedule(Context context) {
        SharedPreferences prefs = Native.prefs(context);
        AlarmReceiver.cancel(context, intent(context));
        long next = nextRun(prefs.getString("exportRuns", null), System.currentTimeMillis());
        if (next > 0) AlarmReceiver.setAlarm(context, next, intent(context));
    }

    /** Copies the staged backup now, records the result, and schedules the next run. */
    static void run(Context context) {
        SharedPreferences prefs = Native.prefs(context);
        JSONObject result = new JSONObject();
        try {
            result.put("at", iso(new Date()));
            File file = write(context, prefs.getBoolean("exportOneFile", false));
            result.put("path", "Documents/" + FOLDER + "/" + file.getName());
        } catch (Exception e) {
            try {
                result.put("error", e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName());
            } catch (Exception ignored) {
                // JSONObject.put only fails on a null key
            }
        }
        prefs.edit().putString("exportResult", result.toString()).apply();
        schedule(context);
    }

    /**
     * One file a day, karteikasten-YYYY-MM-DD.json, which a later run that day replaces; or
     * with oneFile karteikasten.json, which every run replaces. The same names as the app's
     * own export (src/lib/store/backup.ts).
     */
    private static File write(Context context, boolean oneFile) throws Exception {
        File staged = new File(context.getFilesDir(), STAGED);
        if (!staged.isFile()) throw new Exception("no backup to copy yet; open the app once");
        File folder = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS), FOLDER);
        if (!folder.isDirectory() && !folder.mkdirs()) throw new Exception("cannot create " + folder);
        String day = new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(new Date());
        File file = new File(folder, oneFile ? "karteikasten.json" : "karteikasten-" + day + ".json");
        try (InputStream in = new FileInputStream(staged); OutputStream out = new FileOutputStream(file)) {
            byte[] buffer = new byte[64 * 1024];
            for (int n; (n = in.read(buffer)) > 0; ) out.write(buffer, 0, n);
        } catch (FileNotFoundException e) {
            // Android 11 and newer let only the app that made a file replace it, so one an
            // earlier install left cannot be written over.
            if (file.exists() && String.valueOf(e.getMessage()).contains("EACCES")) {
                throw new Exception("cannot replace Documents/" + FOLDER + "/" + file.getName() + ", which an earlier install left; delete it in a file manager");
            }
            throw e;
        }
        return file;
    }

    private static long nextRun(String runs, long now) {
        if (runs == null) return 0;
        try {
            JSONArray list = new JSONArray(runs);
            for (int i = 0; i < list.length(); i++) {
                long at = list.getLong(i);
                if (at > now) return at;
            }
        } catch (Exception e) {
            // a plan the app rewrites when it next goes to the background
        }
        return 0;
    }

    static String iso(Date at) {
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.ROOT);
        format.setTimeZone(TimeZone.getTimeZone("UTC"));
        return format.format(at);
    }

    private static PendingIntent intent(Context context) {
        Intent intent = new Intent(context, AlarmReceiver.class).setAction(AlarmReceiver.EXPORT);
        return PendingIntent.getBroadcast(context, 1, intent, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }
}
