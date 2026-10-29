#!/usr/bin/env bash
# Build PractRand and TestU01 outside the repository (feature 003 T019; research R6, R7, R11).
# Run in WSL after the owner-approved downloads were extracted:
#   bash fast/build_tools.sh practrand ~/downloads/practrand-0.96/PractRand
#   bash fast/build_tools.sh testu01   ~/downloads/testu01-1.2.3/TestU01-1.2.3
# Outputs: ~/practrand/ (RNG_test) and ~/testu01/ (include/, lib/). Each step is echoed so the
# exact commands appear in the build log.
set -euo pipefail
tool="$1"
src="$(cd "$2" && pwd)"

case "$tool" in
practrand)
    out="$HOME/practrand"
    mkdir -p "$out/obj"
    cd "$out/obj"
    set -x
    g++ -c "$src"/src/*.cpp "$src"/src/RNGs/*.cpp "$src"/src/RNGs/other/*.cpp -O3 \
        -I"$src/include" -Wno-constant-logical-operand
    ar rcs "$out/PractRand.a" ./*.o
    g++ -o "$out/RNG_test" "$src/tools/RNG_test.cpp" "$out/PractRand.a" -O3 \
        -I"$src/include" -I"$src/tools" -pthread
    ;;
testu01)
    out="$HOME/testu01"
    work="$HOME/testu01-build"
    rm -rf "$work"
    cp -r "$src" "$work"
    cd "$work"
    set -x
    ./configure --prefix="$out" CFLAGS="-O2 -std=gnu89"
    make -j8
    make install
    ;;
*)
    echo "usage: build_tools.sh practrand|testu01 SOURCE_DIR" >&2
    exit 2
    ;;
esac
