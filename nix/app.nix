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

  # The deck is deployed separately; only the generated font and icons join the build.
  preBuild = ''
    mkdir -p public
    cp -r --no-preserve=mode ${assets} public/generated
  '';

  installPhase = ''
    runHook preInstall
    cp -r dist $out
    runHook postInstall
  '';
}
