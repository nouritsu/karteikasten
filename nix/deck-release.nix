# `nix run .#deck-release -- [--deck VERSION] [--repo OWNER/NAME] [--pack-only]` (D68):
# packs a public deck from data/dist/deck (by default the one latest.json names) into a
# reproducible tarball in out/deck/, uploads it as the GitHub release deck-VERSION, and
# pins it in nix/deck.json, which the release APK then bundles. --pack-only stops after
# the tarball. The upload needs `gh auth login`.
{
  lib,
  writers,
  coreutils,
  gh,
  git,
  gnutar,
  gzip,
  jq,
  nix,
}:
writers.writeFishBin "karteikasten-deck-release" ''
  argparse 'deck=' 'repo=' pack-only -- $argv; or exit 2
  set -gx PATH ${lib.makeBinPath [coreutils gh git gnutar gzip jq nix]} $PATH

  set -l root (git rev-parse --show-toplevel 2>/dev/null)
  if not test -f "$root/flake.nix"
      echo "deck-release: run this inside the karteikasten repository" >&2
      exit 1
  end
  set -l decks $root/data/dist/deck
  set -l deck $_flag_deck
  if test -z "$deck"
      set deck (jq -r .version $decks/latest.json); or exit 1
  end
  if not test -f $decks/$deck/manifest.json
      echo "deck-release: no deck at $decks/$deck; build one with nix run .#build -- --profile public" >&2
      exit 1
  end
  # Only a public deck ships: it leaves out NC and ND items (D26).
  set -l profile (jq -r .profile $decks/$deck/manifest.json)
  if test "$profile" != public
      echo "deck-release: $deck was built with the $profile profile; build it with nix run .#build -- --profile public" >&2
      exit 1
  end

  # The same bytes from the same deck: sorted, no owners or times, gzip without a name.
  set -l name karteikasten-deck-$deck
  set -l tarball $root/out/deck/$name.tar.gz
  mkdir -p (path dirname $tarball)
  tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner --mode=u+rw,go+r,go-w \
      -C $decks --transform "s,^$deck,$name," -cf - $deck | gzip -n -9 >$tarball; or exit 1
  echo "$tarball ("(du -h $tarball | string split -f1 \t)")"
  if set -q _flag_pack_only
      exit 0
  end

  set -l repo $_flag_repo
  if test -z "$repo"
      set repo (gh repo view --json nameWithOwner --jq .nameWithOwner); or exit 1
  end
  gh release create deck-$deck $tarball --repo $repo --latest=false \
      --title "Deck $deck" \
      --notes "The public deck $deck, which nix/deck.json pins for the APK. Built from the sources in sources.lock.json; see THIRD_PARTY_NOTICES.md and the app's Info → Sources."; or exit 1

  # The hash Nix checks: of the unpacked tree, as fetchzip unpacks it.
  set -l url https://github.com/$repo/releases/download/deck-$deck/$name.tar.gz
  set -l hash (nix store prefetch-file --unpack --json $url | jq -r .hash); or exit 1
  jq -n --arg version $deck --arg url $url --arg hash $hash '{version: $version, url: $url, hash: $hash}' >$root/nix/deck.json
  echo "Pinned in nix/deck.json: $deck"
''
