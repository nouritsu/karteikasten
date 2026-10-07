# Generated app assets, so no binaries live in git:
# - Iosevka (SIL OFL 1.1, no Reserved Font Name) subset to the scripts the app shows;
# - the ⏾ ☼ 🕮 icons from Noto Sans Symbols 2 (SIL OFL 1.1): Iosevka lacks 🕮 and
#   draws the moon and sun too small;
# - PWA icons rendered from app/icon.svg;
# - the Android launcher icons from the same file (D40): 48 dp legacy icons and the
#   108 dp adaptive foreground, whose card already sits in the central safe zone.
# In development: nix build .#app-assets -o app/public/generated
{
  fetchurl,
  iosevka-bin,
  lib,
  noto-fonts,
  python3,
  runCommand,
  vips,
}: let
  license = fetchurl {
    url = "https://raw.githubusercontent.com/be5invis/Iosevka/v${iosevka-bin.version}/LICENSE.md";
    hash = "sha256-S6U8fByzknmq5fjX0iBUxIXHEWmSDlo27QmLEV4uPF0=";
  };
  # Basic Latin to Latin Extended-A; IPA Extensions, Spacing Modifier Letters and
  # Combining Diacritical Marks (German IPA uses ◌̯ ◌̩ and the tie in t͡s);
  # General Punctuation; Box Drawing and Block Elements; ≈ for the cognate line;
  # and the icons the app draws instead of emoji, none of which has an emoji
  # form: ⌕ ⓘ ▣ ▤ ▥ ▦ ♪ ⚯ ⛭ (¶ is in Latin-1).
  unicodes = lib.concatStringsSep "," [
    "U+0000-017F"
    "U+0250-036F"
    "U+2000-206F"
    "U+2500-259F"
    "U+2248"
    "U+2315"
    "U+24D8"
    "U+25A3-25A6"
    "U+266A"
    "U+26AF"
    "U+26ED"
  ];
  # Android density buckets and their scale over mdpi.
  densities = {
    mdpi = 1;
    hdpi = 1.5;
    xhdpi = 2;
    xxhdpi = 3;
    xxxhdpi = 4;
  };
  launcherIcons = lib.concatStrings (lib.mapAttrsToList (density: scale: let
      dir = "$out/android/mipmap-${density}";
      px = dp: toString (builtins.ceil (dp * scale));
    in ''
      mkdir -p ${dir}
      vips thumbnail ${../app/icon.svg} "${dir}/ic_launcher.png[strip]" ${px 48}
      cp ${dir}/ic_launcher.png ${dir}/ic_launcher_round.png
      vips thumbnail ${../app/icon.svg} "${dir}/ic_launcher_foreground.png[strip]" ${px 108}
    '')
    densities);
  subset = weight: ''
    pyftsubset ${iosevka-bin}/share/fonts/truetype/Iosevka-${weight}.ttc \
      --font-number=0 --unicodes=${unicodes} --flavor=woff2 \
      --name-IDs='*' --name-languages='*' \
      --output-file=$out/fonts/iosevka-${lib.toLower weight}.woff2
  '';
in
  runCommand "karteikasten-app-assets" {
    nativeBuildInputs = [
      (python3.withPackages (ps: [
        ps.fonttools
        ps.brotli
      ]))
      vips
    ];
  } ''
    mkdir -p $out/fonts $out/icons
    ${subset "Regular"}
    ${subset "Bold"}
    cp ${license} $out/fonts/LICENSE.md
    pyftsubset ${noto-fonts}/share/fonts/noto/NotoSansSymbols2-Regular.otf \
      --unicodes=U+23FE,U+263C,U+1F56E --flavor=woff2 --output-file=$out/fonts/symbols.woff2
    cp ${noto-fonts.src}/fonts/LICENSE $out/fonts/LICENSE-noto.txt
    for size in 192 512; do
      vips thumbnail ${../app/icon.svg} "$out/icons/icon-$size.png[strip]" $size
    done
    ${launcherIcons}
  ''
