{
  lib,
  rustPlatform,
}: let
  cargoToml = lib.importTOML ../curate/Cargo.toml;
in
  rustPlatform.buildRustPackage {
    pname = cargoToml.package.name;
    inherit (cargoToml.package) version;
    src = lib.fileset.toSource {
      root = ../curate;
      fileset = lib.fileset.unions [
        ../curate/Cargo.toml
        ../curate/Cargo.lock
        ../curate/src
      ];
    };
    cargoLock.lockFile = ../curate/Cargo.lock;
    meta.mainProgram = "curate";
  }
