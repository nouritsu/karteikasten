{
  lib,
  assets,
  buildNpmPackage,
  importNpmLock,
}:
buildNpmPackage {
  pname = "karteikasten-app";
  inherit (lib.importJSON ../app/package.json) version;
  src = ../app;

  # Fetches each package by its package-lock.json integrity hash: no npmDepsHash to bump.
  npmDeps = importNpmLock {npmRoot = ../app;};
  inherit (importNpmLock) npmConfigHook;

  # The generated fonts and the third-party notices (Info's Lizenzen shows them) join the
  # build: the deck comes in with the APK, and the Android icons go to its res/ (nix/apk.nix).
  preBuild = ''
    mkdir -p public
    cp -r --no-preserve=mode ${assets} public/generated
    rm -r public/generated/android
    cp ${../THIRD_PARTY_NOTICES.md} public/THIRD_PARTY_NOTICES.md
  '';

  installPhase = ''
    runHook preInstall
    cp -r dist $out
    runHook postInstall
  '';
}
