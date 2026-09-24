![Logo](contrib/electrum-digibyte-logo.svg)

# Electrum-DigiByte

This repository is the DigiByte client based on Electrum. It is being built
incrementally and keeps the upstream Electrum sources available through the
`upstream` Git remote.

## Current milestone

`DGB-ELECTRUM-DIGIBYTE-CONSENSUS-HEADERS` — live header synchronization and
runtime validation milestone.

Completed so far:

- DigiByte mainnet parameters and address prefixes are defined.
- The client default network is DigiByte.
- The DigiByte electrs TCP port is `50011` (`50012` for TLS).
- POSIX client data is stored below `$HOME/.electrum-digibyte`.
- Production `servers.json` is intentionally empty. Users select their own
  electrs server; no private LAN endpoint is embedded in the client.
- A persistent `run_digibyte` launcher is provided.
- The existing Qt GUI launches with DigiByte selected and uses the DigiByte
  data directory.
- The official 23,500,000-header DigiByte checkpoint is used as the bootstrap
  baseline, with independent source/hash verification documented below.
- Near-tip DigiByte header validation uses native batches and worker threads so
  daemon RPC and the GUI remain responsive.
- The DigiByte difficulty context is extended incrementally; live synchronization
  no longer rereads the complete header file for every new block.

The wallet must connect to a running Electrum protocol server that indexes the
DigiByte blockchain. The recommended endpoint is the DigiByte-modified electrs
service, normally published on port `50011`; another Electrum-compatible server
may be used if it indexes DigiByte and implements the required DigiByte network
behavior. A standard Bitcoin electrum server is not compatible, even if it is
reachable on the same port.

## Building the DigiByte wallet stack

The complete self-hosted structure is:

```text
DigiByte full node
        |
        | RPC 14022 / P2P 12024
        v
DigiByte-indexing electrs
        |
        | Electrum protocol, normally host port 50011
        v
Electrum-DigiByte wallet
```

To build this stack, first run a synchronized DigiByte full node with
transaction indexing enabled (`txindex=1`). Then run an electrs server adapted
for DigiByte and configured to connect to that node. Finally configure this
wallet to connect to the electrs endpoint, normally:

```text
<electrs-host>:50011:t
```

The public companion repository contains the DigiByte electrs implementation,
Docker image configuration, and TrueNAS/Linux deployment instructions:

[DigiByte electrs — public repository](https://github.com/digibyte-electrum/electrs)

The electrs service indexes DigiByte transactions and provides fast wallet
queries. It does not replace the full node, and the wallet does not connect to
the node's RPC port directly. The wallet must use an Electrum server indexing
DigiByte, not a normal Bitcoin electrum server.

For container deployments, place the node and electrs on the same private
Docker network. The electrs container can reach the node through the service
name `digibyte`, while the wallet connects through the host's published electrs
port `50011`. Start the node first, wait for blockchain and `txindex`
synchronization, then start electrs and wait for its index to build before using
the wallet for balance, history, or transfer operations. See the companion
repository for the complete Compose examples.

## Runtime milestone — 2026-09-23

A GUI runtime test reached local height `24,261,697`, equal to the connected
electrs server height, and displayed the green synchronized status indicator.
This confirms that the checkpoint-based chain and live post-checkpoint
validation path can catch up successfully.

## Wallet transaction milestone — 2026-09-24

The synchronized GUI wallet successfully received and sent DigiByte in an
operator smoke test. The wallet displayed the received balance and confirmed
transaction correctly. A DigiByte-specific UTXO display regression was also
fixed: block heights above the legacy three-byte ShortID limit now render as a
readable `heightxtransaction-positionxoutput-index` value instead of crashing
the GUI. The transaction test file passes 153 tests and 24 subtests.

## DigiByte visual branding

The README uses the matching `contrib/electrum-digibyte-logo.svg` mark, with
the official DigiByte symbol at the center and the text “electrum DigiByte
wallet”.

The wallet uses the official DigiByte symbol icon for on-chain coin indicators.
The Electrum application, QR-code center mark, and wizard imagery retain their
original Electrum artwork. The DigiByte asset
is copied from the official [DigiByte Core logo repository](https://github.com/DigiByte-Core/digibyte-logos),
specifically `Symbol Icons/512x512.png`. That repository documents the
DigiByte palette, recommends using its supplied artwork without distortion,
and distributes the collection under the MIT License.

Only visible artwork is branded. Internal Electrum module names, Bitcoin
script/address implementation names, and URI/protocol identifiers remain
unchanged where they are required for compatibility.

## Runtime and system dependencies

The client requires Python 3.10 or newer and the Python packages in the
upstream requirements together with the DigiByte development additions:

```bash
.venv/bin/pip install -r contrib/requirements/requirements.txt
.venv/bin/pip install -r contrib/requirements/requirements-digibyte-dev.txt
```

For the Qt desktop GUI, install PyQt6 and the native secp256k1 library/build
tools. On Ubuntu:

```bash
sudo apt update
sudo apt install \
  python3-venv python3-dev python3-pyqt6 \
  libsecp256k1-dev automake libtool
```

### Native DigiByte PoW library — source builds only

This step is required only when compiling and running Electrum-DigiByte from
this source repository. Bundled or packaged applications include the native
library and do not require the user to install a compiler or DigiByte Core
source code.

The DigiByte header validator uses a project-local native PoW library. Building
it requires a C++17-or-newer compiler and a local checkout of the official
DigiByte Core source. The full DigiByte Core daemon does not need to be built;
the source files are used to compile the validator library:

```bash
git clone https://github.com/DigiByte-Core/digibyte.git ~/src/digibyte-core

DIGIBYTE_CORE_DIR="$HOME/src/digibyte-core" \
  ./contrib/build_digibyte_pow.sh
```

The command creates `.build/libdigibytepow.so`. The source launcher loads this
library automatically. If it is stored elsewhere, set
`DIGIBYTE_POW_LIBRARY=/path/to/libdigibytepow.so` before starting the client.

QR scanning is optional. To enable the QR scanner on Ubuntu, install its
runtime library:

```bash
sudo apt install libzbar0
```

Without `libzbar0`, the wallet and Preferences still work, but camera/QR
scanning is unavailable. `libzbar-dev` is not required for normal use.

## Development setup

The project-local development environment is kept in the ignored `.venv/` and
`.build/` directories, so no persistent tooling is stored under `/tmp`.
Additional project development packages are listed in:

```text
contrib/requirements/requirements-digibyte-dev.txt
```

If the local environment has already been prepared, run the client with:

```bash
./run_digibyte --help
```

`run_digibyte` supplies the project-local libsecp256k1 library path and uses
the project virtual environment.

For source builds, the DigiByte PoW adapter is built from an official DigiByte
Core source checkout:

```bash
DIGIBYTE_CORE_DIR=/path/to/digibyte-core ./contrib/build_digibyte_pow.sh
```

This builds the ignored project-local `.build/libdigibytepow.so`. A C++17/20
compiler is required. The client has a batched multi-algorithm PoW adapter and
DigiByte V1--V4 context-aware difficulty validation. It is currently
synchronizing real mainnet headers beyond height 10,000,000 during operator
testing.

## Upgrading from upstream Electrum

The `upstream` remote points to the official Electrum repository, while
`origin` points to this DigiByte fork. The `digi` branch contains the DigiByte
implementation and should be updated through a dedicated upgrade branch.

Before starting an upgrade, make sure the working tree is clean and record the
current test result:

```bash
git switch digi
git status
git fetch upstream --tags
```

For an upstream release tag, create an upgrade branch and merge the release:

```bash
git switch -c upgrade/electrum-X.Y.Z digi
git merge --no-ff X.Y.Z
```

For development work before a release, merge `upstream/master` instead:

```bash
git switch -c upgrade/electrum-master digi
git merge --no-ff upstream/master
```

Resolve conflicts by preserving the upstream behavior first, then reapplying
the DigiByte-specific network parameters, difficulty/PoW validation,
checkpoint handling, data directory, GUI branding, and test changes. Do not
rebase the published `digi` branch; the merge commit keeps the upstream and
DigiByte histories auditable.

After resolving conflicts, run the focused DigiByte tests and the relevant
upstream tests, inspect the difference from upstream, and perform a GUI smoke
test. When the upgrade is validated, merge it into `digi` and push both the
upgrade branch and `digi`:

```bash
git diff upstream/master...HEAD
export LD_LIBRARY_PATH="$PWD/.build/libsecp${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
.venv/bin/pytest -q tests/test_simple_config.py tests/test_digibyte.py tests/test_network.py
git switch digi
git merge --no-ff upgrade/electrum-X.Y.Z
git push origin upgrade/electrum-X.Y.Z digi
```

Each upgrade must re-check the official DigiByte Core checkpoint source and
verify the embedded checkpoint header before release.

Header validation preserves sparse per-algorithm history, refreshes cached
context safely, and matches Core's signed arithmetic and V3/V4 timespan
bounds. DigiByte mainnet uses the latest checkpoint published by the official
DigiByte Core organization, at height 23,500,000. Headers after that
checkpoint retain PoW validation; the first 145 headers warm the difficulty
context before exact V4 validation resumes. The checkpoint source and complete
80-byte header must be independently checked against DigiByte Core before any
release changes these values.

## Tests

Run the DigiByte and related upstream-focused tests with:

```bash
export LD_LIBRARY_PATH="$PWD/.build/libsecp${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
.venv/bin/pytest -q \
  tests/test_simple_config.py \
  tests/test_digibyte.py \
  tests/test_bitcoin.py \
  tests/test_network.py
```

The current baseline is 112 passing tests and 17 subtests.

## Local electrs smoke test

The wallet does not index transaction history by itself. It must connect to a
running Electrum server that is indexing DigiByte, such as the modified electrs
deployment documented in the companion electrs repository. The usual local
endpoint is `192.168.1.66:50011:t`, where `50011` is the host-side port mapped
to the electrs Electrum service. Replace the example address with the DigiByte
Electrum server selected by the operator; do not use a Bitcoin-indexing server.

The server endpoint must be supplied explicitly for a local test:

```bash
./run_digibyte \
  --digibyte \
  daemon -d \
  -s 192.168.1.66:50011:t \
  -1

./run_digibyte --digibyte getinfo
./run_digibyte --digibyte stop
```

Command-specific options such as `-s` and `-1` must appear after `daemon`.
The endpoint above is only a local test example and is not production
configuration.

For repeatable full query validation, provide the endpoint and a DigiByte
address manually:

```bash
./contrib/testing/digibyte_protocol_smoke.sh \
  192.168.1.66:50011:t \
  <DigiByte-address>
```

The script waits for a connected daemon and queries address history, balance,
and unspent outputs. It does not store the endpoint in client configuration.

## Milestone log

Update this section as the client implementation advances:

- [x] DigiByte client network foundation and local electrs smoke test.
- [x] Wallet address-format primitives and BIP44 path compatibility.
- [x] Full standard wallet creation and restore compatibility.
- [x] Qt GUI smoke test and DigiByte data-directory validation.
- [x] Live Electrum protocol connection and daemon `getinfo` validation against operator-selected electrs.
- [x] DigiByte multi-algorithm PoW dispatch and V1--V4 difficulty validation path.
- [x] Batched native PoW verification for faster initial header synchronization.
- [x] Operator smoke test confirmed verified header synchronization reaching height 80,639.
- [x] Operator runtime validation confirmed synchronization progressing toward height 2,000,000.
- [x] Wallet balance, receive, and send smoke test against the synchronized wallet.
- [ ] Complete full header synchronization validation and packaging updates.
- [x] Trusted checkpoint/header bootstrap for faster first launch (operator checkpoint pending independent Core verification).

---

# Electrum - Lightweight Bitcoin client

```
Licence: MIT Licence
Author: Thomas Voegtlin
Language: Python (>= 3.10)
Homepage: https://electrum.org/
```

[![Build Status](https://github.com/spesmilo/electrum/actions/workflows/builds.yml/badge.svg?branch=master)](https://github.com/spesmilo/electrum/actions/workflows/builds.yml)
[![Test coverage statistics](https://coveralls.io/repos/github/spesmilo/electrum/badge.svg?branch=master)](https://coveralls.io/github/spesmilo/electrum?branch=master)
[![Help translate Electrum online](https://d322cqt584bo4o.cloudfront.net/electrum/localized.svg)](https://crowdin.com/project/electrum)


## Getting started

_(If you've come here looking to simply run Electrum,
[you may download it here](https://electrum.org/#download).)_

Electrum itself is pure Python, and so are most of the required dependencies,
but not everything. The following sections describe how to run from source, but here
is a TL;DR:

```
$ sudo apt-get install libsecp256k1-dev
$ ELECTRUM_ECC_DONT_COMPILE=1 python3 -m pip install --user ".[gui,crypto]"
```

### Not pure-python dependencies

#### Qt GUI

If you want to use the Qt interface, install the Qt dependencies:
```
$ sudo apt-get install python3-pyqt6
```

#### libsecp256k1

For elliptic curve operations,
[libsecp256k1](https://github.com/bitcoin-core/secp256k1)
is a required dependency.

If you "pip install" Electrum, by default libsecp will get compiled locally,
as part of the `electrum-ecc` dependency. This can be opted-out of,
by setting the `ELECTRUM_ECC_DONT_COMPILE=1` environment variable.
For the compilation to work, besides a C compiler, you need at least:
```
$ sudo apt-get install automake libtool
```
If you opt out of the compilation, you need to provide libsecp in another way, e.g.:
```
$ sudo apt-get install libsecp256k1-dev
```

#### cryptography

Due to the need for fast symmetric ciphers,
[cryptography](https://github.com/pyca/cryptography) is required.
Install from your package manager (or from pip):
```
$ sudo apt-get install python3-cryptography
```

#### hardware-wallet support

If you would like hardware wallet support,
[see this](https://github.com/spesmilo/electrum-docs/blob/master/hardware-linux.rst).


### Running from tar.gz

If you downloaded the official package (tar.gz), you can run
Electrum from its root directory without installing it on your
system; all the pure python dependencies are included in the 'packages'
directory. To run Electrum from its root directory, just do:
```
$ ./run_electrum
```

You can also install Electrum on your system, by running this command:
```
$ sudo apt-get install python3-setuptools python3-pip
$ python3 -m pip install --user .
```

This will download and install the Python dependencies used by
Electrum instead of using the 'packages' directory.
It will also place an executable named `electrum` in `~/.local/bin`,
so make sure that is on your `PATH` variable.


### Development version (git clone)

_(For OS-specific instructions, see [here for Windows](contrib/build-wine/README_windows.md),
and [for macOS](contrib/osx/README_macos.md))_

Check out the code from GitHub:
```
$ git clone https://github.com/spesmilo/electrum.git
$ cd electrum
$ git submodule update --init
```

Run install (this should install dependencies):
```
$ python3 -m pip install --user -e .
```

Create translations (optional):
```
$ sudo apt-get install gettext
$ ./contrib/locale/build_locale.sh electrum/locale/locale electrum/locale/locale
```

Finally, to start Electrum:
```
$ ./run_electrum
```

### Run tests

Run unit tests with `pytest`:
```
$ pytest tests -v
```
(can be parallelized with `-n auto` option, using [`pytest-xdist`](https://github.com/pytest-dev/pytest-xdist) plugin)

To run a single file, specify it directly like this:
```
$ pytest tests/test_bitcoin.py -v
```

## Creating Binaries

- [Linux (tarball)](contrib/build-linux/sdist/README.md)
- [Linux (AppImage)](contrib/build-linux/appimage/README.md)
- [macOS](contrib/osx/README.md)
- [Windows](contrib/build-wine/README.md)
- [Android](contrib/android/Readme.md)


## Contributing

Any help testing the software, reporting or fixing bugs, reviewing pull requests
and recent changes, writing tests, or helping with outstanding issues is very welcome.
Implementing new features, or improving/refactoring the codebase, is of course
also welcome, but to avoid wasted effort, especially for larger changes,
we encourage discussing these on the issue tracker or IRC first.

Besides [GitHub](https://github.com/spesmilo/electrum),
most communication about Electrum development happens on IRC, in the
`#electrum` channel on Libera Chat. The easiest way to participate on IRC is
with the web client, [web.libera.chat](https://web.libera.chat/#electrum).

Please improve translations on [Crowdin](https://crowdin.com/project/electrum).
