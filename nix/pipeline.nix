{
  lib,
  python3,
}: let
  inherit (lib.importTOML ../pipeline/pyproject.toml) project;
  dependencies = ps: [
    ps.duckdb
    ps.httpx
  ];
in
  python3.pkgs.buildPythonApplication {
    pname = project.name;
    inherit (project) version;
    pyproject = true;
    src = lib.fileset.toSource {
      root = ../pipeline;
      fileset = lib.fileset.unions [
        ../pipeline/pyproject.toml
        ../pipeline/karteikasten_pipeline
        ../pipeline/tests
      ];
    };
    build-system = [python3.pkgs.setuptools];
    dependencies = dependencies python3.pkgs;
    nativeCheckInputs = [python3.pkgs.pytestCheckHook];
    # Tests run in the flake's checks.pipeline, so `nix run` never waits on them.
    doCheck = false;

    # Python with the runtime and test dependencies, for the dev shell.
    passthru.devEnv = python3.withPackages (ps: dependencies ps ++ [ps.pytest]);

    meta.mainProgram = "karteikasten-pipeline";
  }
