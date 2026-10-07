{
  description = "Karteikasten: flashcards for the most frequent German words, as an Android app";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    inherit (nixpkgs) lib;

    # The desktop runs the pipeline and the curation tool and builds the APK; androidenv's
    # SDK tools only run on x86_64. `own` is this flake's packages for the same system.
    forAllSystems = f:
      lib.genAttrs ["x86_64-linux"] (system:
        f {
          inherit system;
          pkgs = nixpkgs.legacyPackages.${system};
          own = self.packages.${system};
        });
  in {
    packages = forAllSystems ({
      system,
      pkgs,
      ...
    }: let
      # The Android SDK is unfree, and androidenv asks for its licence to be accepted.
      androidPkgs = import nixpkgs {
        inherit system;
        config = {
          allowUnfree = true;
          android_sdk.accept_license = true;
        };
      };
    in rec {
      app = pkgs.callPackage ./nix/app.nix {assets = app-assets;};
      # Font subset and icons; in development: nix build .#app-assets -o app/public/generated
      app-assets = pkgs.callPackage ./nix/app-assets.nix {};
      # Unsigned, with an empty deck unless overridden; `nix run .#apk` bundles the
      # working tree's deck and signs it.
      apk = androidPkgs.callPackage ./nix/apk.nix {
        assets = app-assets;
        web = app;
      };
      # `nix run .#curate` from the working tree: it reads data/work and writes overrides/.
      curate = pkgs.callPackage ./nix/curate.nix {};
      pipeline = pkgs.callPackage ./nix/pipeline.nix {};
    });

    # data/ is gitignored, so it never reaches the flake source: these wrappers run the
    # pipeline CLI against the working tree, which it finds by walking up from $PWD.
    apps = forAllSystems ({
      pkgs,
      own,
      ...
    }: let
      pipelineApp = command: description: {
        type = "app";
        program = lib.getExe (pkgs.writers.writeFishBin "karteikasten-${command}" ''
          exec ${lib.getExe own.pipeline} ${command} $argv
        '');
        meta = {inherit description;};
      };
    in {
      fetch = pipelineApp "fetch" "Snapshot every source into data/raw and update sources.lock.json";
      build = pipelineApp "build" "Build the deck bundle from the data/raw snapshot (stages 20-70)";
      report = pipelineApp "report" "Write coverage and diff reports to reports/";
      apk = {
        type = "app";
        program = lib.getExe (pkgs.callPackage ./nix/apk-app.nix {
          inherit (own) apk;
          flake = self;
        });
        meta.description = "Bundle a deck into the APK, sign it with the debug key, and optionally adb install it";
      };
    });

    devShells = forAllSystems ({
      pkgs,
      own,
      ...
    }: {
      default = pkgs.mkShell {
        packages = [
          # Pipeline: Python + DuckDB, media processing
          own.pipeline.devEnv
          pkgs.duckdb
          pkgs.sqlite
          pkgs.ffmpeg
          pkgs.vips
          # App; qrencode prints the link app/phone.fish serves
          pkgs.nodejs
          pkgs.qrencode
          # Curation tool
          pkgs.cargo
          pkgs.rustc
          pkgs.clippy
          pkgs.rustfmt
          pkgs.rust-analyzer
          # APK: Gradle and a JDK to build app/android by hand, adb to install
          pkgs.gradle
          pkgs.jdk21
          pkgs.android-tools
          # Nix
          pkgs.alejandra
        ];

        ANDROID_HOME = own.apk.sdk;

        RUST_SRC_PATH = "${pkgs.rustPlatform.rustLibSrc}";
      };
    });

    # alejandra over every .nix file. treefmt supplies the paths: `nix fmt` passes
    # none, which bare alejandra would read as "format stdin".
    formatter = forAllSystems ({pkgs, ...}:
      pkgs.treefmt.withConfig {
        name = "alejandra-tree";
        runtimeInputs = [pkgs.alejandra];
        settings = {
          tree-root-file = "flake.nix";
          on-unmatched = "info";
          formatter.alejandra = {
            command = "alejandra";
            options = ["--quiet"];
            includes = ["*.nix"];
          };
        };
      });

    checks = forAllSystems ({
      system,
      pkgs,
      own,
    }: {
      # Formats a copy of the .nix files and fails on any diff.
      formatting = self.formatter.${system}.check (lib.fileset.toSource {
        root = ./.;
        fileset = lib.fileset.fileFilter (file: file.hasExt "nix") ./.;
      });

      pipeline = own.pipeline.overridePythonAttrs {doCheck = true;};

      app = own.app.overrideAttrs {
        pname = "karteikasten-app-check";
        buildPhase = ''
          runHook preBuild
          npm run check
          npm test
          runHook postBuild
        '';
        installPhase = "touch $out";
      };

      # Building the package runs `cargo test`.
      inherit (own) curate;

      # With the stub deck: Gradle still builds offline from nix/apk-deps.json.
      inherit (own) apk;

      curate-clippy = own.curate.overrideAttrs (old: {
        pname = "${old.pname}-clippy";
        nativeBuildInputs = old.nativeBuildInputs ++ [pkgs.clippy];
        buildPhase = ''
          runHook preBuild
          cargo clippy --offline --all-targets -- --deny warnings
          runHook postBuild
        '';
        doCheck = false;
        installPhase = "touch $out";
      });
    });
  };
}
