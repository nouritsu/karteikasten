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

  # Only the generated fonts join the build: the deck comes in with the APK, and the
  # Android launcher icons go to its res/ (nix/apk.nix).
  preBuild = ''
    mkdir -p public
    cp -r --no-preserve=mode ${assets} public/generated
    rm -r public/generated/android
  '';

  installPhase = ''
    runHook preInstall
    cp -r dist $out
    runHook postInstall
  '';
}
