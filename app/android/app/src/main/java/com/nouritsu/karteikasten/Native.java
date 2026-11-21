package com.nouritsu.karteikasten;

import android.Manifest;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;

/**
 * The web app's handle on its Android side (src/lib/native.ts): the backup it stages and
 * the export runs it plans (Exports), the reminders it plans (Reminders), and the cloud
 * backup switch (CloudBackupAgent), all kept in this app's own SharedPreferences.
 */
@CapacitorPlugin(
    name = "Native",
    permissions = { @Permission(alias = "notifications", strings = { Manifest.permission.POST_NOTIFICATIONS }) }
)
public class Native extends Plugin {

    static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences("karteikasten", Context.MODE_PRIVATE);
    }

    @Override
    protected void handleOnResume() {
        // The app is in front: a reminder that is still showing has done its job.
        Reminders.clear(getContext());
    }

    /** Saves the backup the export alarm copies. */
    @PluginMethod
    public void stage(PluginCall call) {
        String json = call.getString("json");
        if (json == null) {
            call.reject("no backup");
            return;
        }
        File target = new File(getContext().getFilesDir(), Exports.STAGED);
        File part = new File(getContext().getFilesDir(), Exports.STAGED + ".part");
        try (Writer out = new OutputStreamWriter(new FileOutputStream(part), StandardCharsets.UTF_8)) {
            out.write(json);
        } catch (Exception e) {
            call.reject(e.getMessage());
            return;
        }
        // Written aside and moved into place, so an alarm never copies half a file.
        if (!part.renameTo(target)) {
            call.reject("cannot move " + part + " into place");
            return;
        }
        call.resolve();
    }

    /** The export run times (epoch ms, ascending) and whether to keep one file. */
    @PluginMethod
    public void planExports(PluginCall call) {
        JSArray runs = call.getArray("runs", new JSArray());
        prefs(getContext()).edit()
            .putString("exportRuns", runs.toString())
            .putBoolean("exportOneFile", Boolean.TRUE.equals(call.getBoolean("oneFile", false)))
            .apply();
        Exports.schedule(getContext());
        call.resolve();
    }

    /** How the last regular export went: { at, path } or { at, error }, or nothing yet. */
    @PluginMethod
    public void lastExport(PluginCall call) {
        String result = prefs(getContext()).getString("exportResult", null);
        JSObject out = new JSObject();
        out.put("result", result);
        call.resolve(out);
    }

    /** The reminders to post: [{ at, title, text }], ascending. */
    @PluginMethod
    public void planReminders(PluginCall call) {
        JSArray items = call.getArray("items", new JSArray());
        prefs(getContext()).edit().putString("reminders", items.toString()).apply();
        Reminders.schedule(getContext());
        call.resolve();
    }

    /** Whether notifications may be posted; on Android 13 and newer, asks once if not yet. */
    @PluginMethod
    public void askNotifications(PluginCall call) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU || getPermissionState("notifications") == PermissionState.GRANTED) {
            resolveAllowed(call, true);
        } else {
            requestPermissionForAlias("notifications", call, "notificationsAnswered");
        }
    }

    @PermissionCallback
    private void notificationsAnswered(PluginCall call) {
        resolveAllowed(call, getPermissionState("notifications") == PermissionState.GRANTED);
    }

    private static void resolveAllowed(PluginCall call, boolean allowed) {
        JSObject out = new JSObject();
        out.put("allowed", allowed);
        call.resolve(out);
    }

    @PluginMethod
    public void setCloudBackup(PluginCall call) {
        prefs(getContext()).edit().putBoolean("cloudBackup", Boolean.TRUE.equals(call.getBoolean("on", false))).apply();
        call.resolve();
    }
}
