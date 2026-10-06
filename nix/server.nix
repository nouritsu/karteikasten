# NixOS module, exposed as nixosModules.karteikasten. Stub: routing and TLS only;
# cache headers, MIME types and deck directory ownership come in Phase 7.
self: {
  config,
  lib,
  pkgs,
  ...
}: let
  cfg = config.services.karteikasten;
in {
  options.services.karteikasten = {
    enable = lib.mkEnableOption "the Karteikasten app and deck server";

    hostName = lib.mkOption {
      type = lib.types.str;
      example = "pi.tail0123.ts.net";
      description = "Host name Caddy serves the app under.";
    };

    deckDir = lib.mkOption {
      type = lib.types.path;
      default = "/var/lib/karteikasten/deck";
      description = "Directory with the deck versions and latest.json, served at /deck/.";
    };

    package = lib.mkOption {
      type = lib.types.package;
      default = self.packages.${pkgs.stdenv.hostPlatform.system}.app;
      defaultText = lib.literalMD "the `app` package of this flake";
      description = "Static PWA build served at /.";
    };

    tls = lib.mkOption {
      type = lib.types.enum [
        "tailscale"
        "acme"
      ];
      default = "tailscale";
      description = ''
        Certificate source. `tailscale`: hostName is the machine's *.ts.net name and
        Caddy gets the certificate from tailscaled. `acme`: Caddy's automatic HTTPS.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    services.caddy = {
      enable = true;
      virtualHosts.${cfg.hostName}.extraConfig = ''
        handle_path /deck/* {
          root * ${cfg.deckDir}
          file_server
        }
        handle {
          root * ${cfg.package}
          file_server
        }
      '';
    };

    services.tailscale.permitCertUid = lib.mkIf (cfg.tls == "tailscale") config.services.caddy.user;
  };
}
