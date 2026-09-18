#!/bin/sh
set -eu

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "usage: $0 SERVER ADDRESS [DATA_DIR]" >&2
    echo "example: $0 host.example:50011:t D..." >&2
    exit 2
fi

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
server=$1
address=$2
data_dir=${3:-"${HOME}/.electrum-digibyte"}

client="$project_dir/run_digibyte"

cleanup() {
    "$client" --digibyte -D "$data_dir" stop >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

"$client" --digibyte -D "$data_dir" daemon -d -s "$server" -1

connected=false
i=0
while [ "$i" -lt 30 ]; do
    info=$("$client" --digibyte -D "$data_dir" getinfo 2>/dev/null || true)
    printf '%s\n' "$info"
    if printf '%s\n' "$info" | grep -q '"connected": true'; then
        connected=true
        break
    fi
    i=$((i + 1))
    sleep 1
done

if [ "$connected" != true ]; then
    echo "client did not connect to $server within 30 seconds" >&2
    exit 1
fi

echo "--- address history: $address"
"$client" --digibyte -D "$data_dir" getaddresshistory "$address"
echo "--- address balance: $address"
"$client" --digibyte -D "$data_dir" getaddressbalance "$address"
echo "--- address unspent: $address"
"$client" --digibyte -D "$data_dir" getaddressunspent "$address"
