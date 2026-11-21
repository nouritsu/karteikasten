# The Android APK (D40–D42): the web build and one deck in Capacitor's WebView shell,
# built by Gradle offline. The output is unsigned; `nix run .#apk` signs it with a release
# key or this machine's debug key (D43, D68), so no key ever enters the store.
# After changing Capacitor, AGP or Gradle: nix build .#apk.mitmCache.updateScript && ./result
{
  lib,
  stdenv,
  androidenv,
  assets,
  gradle,
  importNpmLock,
  jdk21,
  nodejs,
  web,
  # One deck version directory, bundled at /deck/ (D41): the deck nix/deck.json pins
  # (nix/deck.nix), the stub for checks, or one from data/dist/deck (nix run .#apk -- --deck).
  bundledDeck ? ./stub-deck,
  # A build that installs beside the release one, as "Karteikasten (debug)" with its own
  # id and storage (D64; app/android/app/build.gradle): `nix run .#apk-debug -- --install`.
  debugApp ? false,
}: let
  name = "karteikasten${lib.optionalString debugApp "-debug"}";
  buildToolsVersion = "35.0.0"; # AGP 8.13's default; any other makes it reach for the network
  android = androidenv.composeAndroidPackages {
    platformVersions = ["36"];
    buildToolsVersions = [buildToolsVersion];
    includeEmulator = false;
    includeSources = false;
    includeSystemImages = false;
    includeNDK = false;
  };
  sdk = "${android.androidsdk}/libexec/android-sdk";
  deckVersion = (lib.importJSON "${bundledDeck}/manifest.json").deck_version;

  # versionCode = MAJOR*10000 + MINOR*100 + PATCH, so 0.2.0 is 200 (D68). Android installs
  # an update only over a lower code, so bumping the version in package.json is all a
  # release needs. A new deck comes with a new version.
  appVersion = (lib.importJSON ../app/package.json).version;
  versionParts = builtins.match "(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)" appVersion;
  versionCode = let
    part = n: lib.toInt (builtins.elemAt versionParts n);
  in
    assert lib.assertMsg (versionParts != null) "app/package.json: version must be plain X.Y.Z, got \"${appVersion}\"";
    assert lib.assertMsg (part 1 < 100 && part 2 < 100) "app/package.json: MINOR and PATCH must stay below 100, got ${appVersion}";
      part 0 * 10000 + part 1 * 100 + part 2;
in
  stdenv.mkDerivation (finalAttrs: {
    pname = "${name}-apk";
    version = "${appVersion}+${deckVersion}";
    src = ../app;

    npmDeps = importNpmLock {npmRoot = ../app;};
    nativeBuildInputs = [
      gradle
      importNpmLock.npmConfigHook
      nodejs
    ];

    mitmCache = gradle.fetchDeps {
      pkg = finalAttrs.finalPackage;
      data = ./apk-deps.json;
      # The Capacitor CLI reads the user's passwd entry, which the update sandbox lacks.
      bwrapFlags = ''--ro-bind "$PWD" "$PWD" --ro-bind /etc/passwd /etc/passwd'';
    };

    ANDROID_HOME = sdk;
    gradleFlags =
      [
        "-Dorg.gradle.java.home=${jdk21}"
        # The aapt2 AGP fetches from Maven is linked for FHS systems and fails on NixOS.
        "-Pandroid.aapt2FromMavenOverride=${sdk}/build-tools/${buildToolsVersion}/aapt2"
        "-PversionCode=${toString versionCode}"
        "-PversionName=${finalAttrs.version}"
        # Release lint looks up newer library versions in Google's Maven indexes and the
        # Play SDK index. Those files change upstream every few days, so pinning them in
        # apk-deps.json broke the build within a week each time.
        "-x"
        "lintVitalRelease"
      ]
      # Only when wanted: Gradle reads any value, "false" too, as set.
      ++ lib.optional debugApp "-PdebugApp=true";
    gradleBuildTask = "assembleRelease";
    # Android variants make the default nixDownloadDeps ambiguous; record a real build.
    gradleUpdateTask = finalAttrs.gradleBuildTask;

    # Runs before the Gradle update script too, so it sees the same project.
    preBuild = ''
      cp -r --no-preserve=mode ${web} dist
      mkdir -p dist/deck
      cp -r --no-preserve=mode ${bundledDeck} dist/deck/${deckVersion}
      echo '{"version": "${deckVersion}"}' > dist/deck/latest.json
      cp -r --no-preserve=mode ${assets}/android/. android/app/src/main/res/
      npx cap sync android
      cd android
    '';

    installPhase = ''
      runHook preInstall
      install -Dm644 app/build/outputs/apk/release/app-release-unsigned.apk \
        $out/${name}-${finalAttrs.version}-unsigned.apk
      runHook postInstall
    '';

    # The signed APK's name in out/apk/ (nix/apk-app.nix): the app's version, without the deck's.
    passthru = {
      inherit deckVersion sdk buildToolsVersion versionCode;
      signedName = "${name}-${appVersion}.apk";
    };

    meta.license = lib.licenses.gpl3Plus;

    meta.sourceProvenance = with lib.sourceTypes; [
      fromSource
      binaryBytecode # Maven artefacts from the mitm cache
    ];
  })
