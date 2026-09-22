# Electrum-DigiByte

This repository is the DigiByte client based on Electrum. It is being built
incrementally and keeps the upstream Electrum sources available through the
`upstream` Git remote.

## Current milestone

`DGB-ELECTRUM-DIGIBYTE-CONSENSUS-HEADERS` — live header synchronization in progress.

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

The DigiByte PoW adapter is built from an official DigiByte Core source
checkout:

```bash
DIGIBYTE_CORE_DIR=/path/to/digibyte-core ./contrib/build_digibyte_pow.sh
```

This builds the ignored project-local `.build/libdigibytepow.so`. A C++17/20
compiler is required. The client has a batched multi-algorithm PoW adapter and
DigiByte V1--V4 context-aware difficulty validation. It is currently
synchronizing real mainnet headers beyond height 10,000,000 during operator
testing.

Header validation preserves sparse per-algorithm history, refreshes cached
context safely, and matches Core's signed arithmetic and V3/V4 timespan
bounds. DigiByte mainnet now includes a pinned bootstrap checkpoint beyond
height 10,000,000. Headers after that checkpoint retain PoW validation; the
first 145 headers warm the difficulty context before exact V4 validation
resumes. The checkpoint must be independently verified against DigiByte Core
before release.

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

The server endpoint must be supplied explicitly for a local test. Replace the
example address with the electrs server selected by the operator:

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
- [ ] Complete full header synchronization and wallet query validation.
- [x] Trusted checkpoint/header bootstrap for faster first launch (operator checkpoint pending independent Core verification).
- [ ] Packaging updates.

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
