#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
core_dir=${DIGIBYTE_CORE_DIR:-}

if [ -z "$core_dir" ] || [ ! -d "$core_dir/src/crypto" ]; then
    echo "Set DIGIBYTE_CORE_DIR to an official DigiByte Core source checkout." >&2
    exit 2
fi

out_dir="$project_dir/.build"
mkdir -p "$out_dir"

if [ -n "${GCC_TRIPLET_HOST:-}" ]; then
    cxx="${GCC_TRIPLET_HOST}-g++"
    output_file=${DIGIBYTE_POW_OUTPUT:-"$out_dir/libdigibytepow-0.dll"}
    linker_flags="-shared -static-libgcc -static-libstdc++"
else
    cxx="g++"
    output_file=${DIGIBYTE_POW_OUTPUT:-"$out_dir/libdigibytepow.so"}
    linker_flags="-shared -fPIC"
fi

"$cxx" $linker_flags -O2 -std=c++20 -pthread \
    -I"$core_dir/src" -I"$core_dir/src/crypto" \
    "$project_dir/contrib/digibyte_pow_adapter.cpp" \
    "$core_dir/src/crypto/sha256.cpp" \
    "$core_dir/src/crypto/hmac_sha256.cpp" \
    "$core_dir/src/crypto/scrypt.cpp" \
    "$core_dir/src/crypto/groestl.cpp" \
    "$core_dir/src/crypto/skein.cpp" \
    "$core_dir/src/crypto/luffa.cpp" \
    "$core_dir/src/crypto/cubehash.cpp" \
    "$core_dir/src/crypto/shavite.cpp" \
    "$core_dir/src/crypto/simd.cpp" \
    "$core_dir/src/crypto/echo.cpp" \
    "$core_dir/src/crypto/keccak.cpp" \
    "$core_dir/src/crypto/KeccakP-800-reference.cpp" \
    "$core_dir/src/crypto/odocrypt.cpp" \
    "$core_dir/src/crypto/aes.cpp" \
    -o "$output_file"

echo "Built $output_file"
