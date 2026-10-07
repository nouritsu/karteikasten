#!/usr/bin/env fish
# Preview the built app in your phone's browser on the home network, with a QR code
# that opens it; quicker than an APK for trying UI changes. The app itself installs
# with `nix run .#apk -- --install` (D40).
# From the dev shell:  app/phone.fish [--ip ADDRESS] [--port PORT] [--no-build]
#
# Listens only on the LAN address, never on Tailscale or other interfaces.

argparse 'ip=' 'port=' no-build -- $argv; or exit 2
set -l port 4173
set -q _flag_port; and set port $_flag_port

# The address on the interface of the default route, unless given.
set -l address $_flag_ip
if test -z "$address"
    set -l device (ip route show default | string match -rg 'dev (\S+)')[1]
    set address (ip -4 -o addr show dev "$device" scope global | string match -rg 'inet ([\d.]+)/')[1]
end
# Only a private home-network address: never a public, VPN or tailnet one.
if not string match -qr '^(10|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.' -- "$address"
    echo "phone.fish: no private LAN address found ('$address'); pass one with --ip" >&2
    exit 1
end

for tool in npm npx qrencode
    if not command -q $tool
        echo "phone.fish: $tool not found; run this inside the dev shell (direnv allow, or nix develop)" >&2
        exit 1
    end
end

cd (status dirname); or exit 1
if not set -q _flag_no_build
    npm run build; or exit 1
end

set -l origin "http://$address:$port"
echo
qrencode -t ansiutf8 -m 2 "$origin/"
echo "Scan it, or open $origin/ on a phone on the same network."
if systemctl is-active --quiet firewall.service
    set -l device (ip -4 -o addr show | string match -rg '^\d+:\s+(\S+)\s+inet '(string escape --style=regex -- $address)'/')[1]
    echo
    echo "If the phone can't connect, the NixOS firewall blocks port $port. Open it until the next reboot with"
    echo "  sudo iptables -I nixos-fw -i $device -p tcp --dport $port -j nixos-fw-accept"
    echo "and close it again with -D in place of -I."
end
echo
exec npx vite preview --host $address --port $port --strictPort
