# Generated app assets, so no binaries live in git:
# - Iosevka (SIL OFL 1.1, no Reserved Font Name) subset to the scripts the app shows;
#   the icons are Material Icons, drawn as SVG (D57; src/lib/ui/Icon.svelte);
# - the Android launcher icons rendered from app/icon.svg (D40, D65): 48 dp legacy icons
#   and the 108 dp adaptive foreground, whose block sits in the central safe zone, and its
#   one-colour twin for themed icons from app/icon-monochrome.svg;
# - the 24 dp status-bar icon for the study reminder (D63), from app/notification.svg.
# In development: nix build .#app-assets -o app/public/generated
{
  fetchurl,
  iosevka-bin,
  lib,
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
  # General Punctuation; Box Drawing and Block Elements (bars, the heatmap). Then every
  # other symbol the app draws; keep this list equal to the symbols in the code.
  unicodes = lib.concatStringsSep "," [
    "U+0000-017F"
    "U+0250-036F"
    "U+2000-206F"
    "U+2500-259F"
    "U+2192" # → in a change (Abdeckung 41% → 42%) and a path to an Android setting
    "U+2212" # − in a deduction (Audio −10)
    "U+2248" # ≈ the cognate line
    "U+25A0" # ■ a colour's square, a legend
    "U+25B2" # ▲ up on the span before (Statistik)
    "U+25BC" # ▼ down on it
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
      vips thumbnail ${../app/icon-monochrome.svg} "${dir}/ic_launcher_monochrome.png[strip]" ${px 108}
      mkdir -p $out/android/drawable-${density}
      vips thumbnail ${../app/notification.svg} "$out/android/drawable-${density}/ic_stat_study.png[strip]" ${px 24}
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
    mkdir -p $out/fonts
    ${subset "Regular"}
    ${subset "Bold"}
    cp ${license} $out/fonts/LICENSE.md
    ${launcherIcons}
  ''
