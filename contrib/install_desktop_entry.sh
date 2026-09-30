#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
data_dir="${XDG_DATA_HOME:-$HOME/.local/share}"
icon_dir="$data_dir/icons/hicolor/scalable/apps"
applications_dir="$data_dir/applications"
desktop_file="$applications_dir/electrum-digibyte.desktop"

if [ "$#" -gt 1 ]; then
    echo "Usage: $0 [path-to-electrum-digibyte-<version>-x86_64.AppImage]" >&2
    exit 2
fi

mkdir -p "$icon_dir" "$applications_dir"
cp "$project_dir/electrum/gui/icons/electrum_digibyte.svg" "$icon_dir/electrum_digibyte.svg"

if [ "$#" -eq 1 ]; then
    executable=$(readlink -f "$1")
    [ -x "$executable" ] || {
        echo "AppImage is not executable: $executable" >&2
        exit 1
    }
else
    executable="$project_dir/run_digibyte"
fi

cat > "$desktop_file" <<EOF
[Desktop Entry]
Comment=Electrum DigiByte Wallet
Exec=$executable --digibyte gui
GenericName=DigiByte Wallet
Icon=electrum_digibyte
Name=Electrum DigiByte Wallet
Categories=Finance;Network;
StartupNotify=true
StartupWMClass=electrum-digibyte
Terminal=false
Type=Application
Keywords=crypto;currency;DigiByte;DGB
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$applications_dir" 2>/dev/null || true
fi

echo "Installed Electrum DigiByte Wallet in $desktop_file"
