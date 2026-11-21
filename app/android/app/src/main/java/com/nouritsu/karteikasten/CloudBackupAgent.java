package com.nouritsu.karteikasten;

import android.app.backup.BackupAgent;
import android.app.backup.BackupDataInput;
import android.app.backup.BackupDataOutput;
import android.app.backup.FullBackupDataOutput;
import android.os.Build;
import android.os.ParcelFileDescriptor;
import java.io.IOException;

/**
 * Android's Auto Backup of the app's data (D62): to the Google account only when
 * Privacy's Cloud backup is on, and always in a direct transfer to a new phone.
 * https://developer.android.com/identity/data/autobackup#ImplementingBackupAgent
 * From fast-track.
 */
public class CloudBackupAgent extends BackupAgent {

    @Override
    public void onFullBackup(FullBackupDataOutput data) throws IOException {
        if (Native.prefs(this).getBoolean("cloudBackup", false) || deviceTransfer(data)) super.onFullBackup(data);
    }

    // Before Android 9 a transfer and a cloud backup look alike, so off backs up nothing.
    private static boolean deviceTransfer(FullBackupDataOutput data) {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.P && (data.getTransportFlags() & FLAG_DEVICE_TO_DEVICE_TRANSFER) != 0;
    }

    // Auto Backup only (fullBackupOnly): the key-value backup is never used.
    @Override
    public void onBackup(ParcelFileDescriptor oldState, BackupDataOutput data, ParcelFileDescriptor newState) {}

    @Override
    public void onRestore(BackupDataInput data, int appVersionCode, ParcelFileDescriptor newState) {}
}
