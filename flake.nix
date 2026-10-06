{
  description = "Karteikasten: flashcards for the most frequent German words, as a phone PWA";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    inherit (nixpkgs) lib;

    # The desktop runs the pipeline and the curation tool; the Pi (aarch64) serves the app.
    # `own` is this flake's packages for the same system.
    forAllSystems = f:
      lib.genAttrs ["x86_64-linux" "aarch64-linux"] (system:
        f {
          inherit system;
          pkgs = nixpkgs.legacyPackages.${system};
          own = self.packages.${system};
        });
  in {
    packages = forAllSystems ({pkgs, ...}: rec {
      app = pkgs.callPackage ./nix/app.nix {assets = app-assets;};
      # Font subset and icons; in development: nix build .#app-assets -o app/public/generated
      app-assets = pkgs.callPackage ./nix/app-assets.nix {};
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
      deploy-deck = pipelineApp "deploy-deck" "Copy a deck bundle to the Pi and update latest.json";
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
          # Nix
          pkgs.alejandra
        ];

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

      # Evaluates the module in a minimal NixOS system and parses the Caddyfile it yields.
      server-module = let
        caddy =
          (lib.nixosSystem {
            modules = [
              self.nixosModules.karteikasten
              {
                nixpkgs.hostPlatform = system;
                system.stateVersion = "26.05";
                services.karteikasten = {
                  enable = true;
                  hostName = "karteikasten.example.ts.net";
                };
              }
            ];
          }).config.services.caddy;
      in
        pkgs.runCommand "karteikasten-server-module" {nativeBuildInputs = [caddy.package];} ''
          export HOME=$TMPDIR
          caddy adapt --config ${caddy.configFile} --adapter caddyfile > /dev/null
          touch $out
        '';
    });

    # Imported by the Pi's system flake.
    nixosModules.karteikasten = import ./nix/server.nix self;
  };
}
