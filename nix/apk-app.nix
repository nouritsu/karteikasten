# `nix run .#apk -- [--deck VERSION] [--version-code N] [--install]` (D42, D43, D45).
# data/ is gitignored, so this runs against the working tree: it bundles a deck from
# data/dist/deck into the flake's apk package, signs the result with this machine's
# Android debug key, and writes it to data/dist/apk/.
{
  lib,
  stdenv,
  writers,
  android-tools,
  coreutils,
  git,
  jdk21,
  jq,
  apk,
  flake,
}:
writers.writeFishBin "karteikasten-apk" ''
  argparse 'deck=' 'version-code=' install -- $argv; or exit 2
  set -gx PATH ${lib.makeBinPath [android-tools coreutils git jdk21 jq]} ${apk.sdk}/build-tools/35.0.0 $PATH

  set -l root (git rev-parse --show-toplevel 2>/dev/null)
  if not test -f "$root/flake.nix"
      echo "apk: run this inside the karteikasten repository" >&2
      exit 1
  end
  set -l decks $root/data/dist/deck

  # The deck that latest.json names, unless given.
  set -l deck $_flag_deck
  if test -z "$deck"
      set deck (jq -r .version $decks/latest.json); or exit 1
  end
  if not test -f $decks/$deck/manifest.json
      echo "apk: no deck at $decks/$deck; build one with nix run .#build" >&2
      exit 1
  end

  # Android installs an update only over a lower versionCode: the commit count
  # rises with every commit, and --version-code covers a new deck without one.
  set -l code $_flag_version_code
  if test -z "$code"
      set code (git -C $root rev-list --count HEAD); or exit 1
  end

  set -l built (nix build --no-link --print-out-paths --impure --expr "
    (builtins.getFlake \"path:${flake}\").packages.${stdenv.hostPlatform.system}.apk.override {
      bundledDeck = builtins.path { path = /. + \"$decks/$deck\"; name = \"karteikasten-deck\"; };
      versionCode = $code;
    }"); or exit 1

  # The SDK's debug key, the same on every build from this machine; keep the file,
  # or phones refuse the next update.
  set -l keystore ~/.android/debug.keystore
  if not test -f $keystore
      mkdir -p (path dirname $keystore)
      keytool -genkeypair -keystore $keystore -storepass android -alias androiddebugkey \
          -keypass android -keyalg RSA -keysize 2048 -validity 10000 \
          -dname 'CN=Android Debug,O=Android,C=US'; or exit 1
  end

  set -l unsigned $built/*.apk
  set -l signed $root/data/dist/apk/(path basename $unsigned | string replace -- -unsigned.apk .apk)
  mkdir -p (path dirname $signed)
  apksigner sign --ks $keystore --ks-pass pass:android --ks-key-alias androiddebugkey \
      --key-pass pass:android --v4-signing-enabled false --out $signed $unsigned; or exit 1
  echo "$signed (versionCode $code)"

  if set -q _flag_install
      adb install -r $signed; or exit 1
  end
''
