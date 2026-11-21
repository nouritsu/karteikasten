# The deck a release bundles (D68). CI can't build one: the pipeline reads gigabytes of
# source snapshots that only data/raw holds. So a public deck is built locally
# (`nix run .#build -- --profile public`), uploaded as a GitHub release by
# `nix run .#deck-release`, and pinned in nix/deck.json by URL and hash. Without a pin,
# the stub deck.
{
  lib,
  fetchzip,
}: let
  pin = lib.importJSON ./deck.json;
in
  if pin ? url
  then
    fetchzip {
      inherit (pin) url hash;
      name = "karteikasten-deck-${pin.version}";
    }
  else ./stub-deck
