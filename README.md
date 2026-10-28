![Logo](contrib/electrum-digibyte-logo.svg)

# Electrum-DigiByte

This repository is the DigiByte client based on Electrum. It is being built
incrementally and keeps the upstream Electrum sources available through the
`upstream` Git remote.

## Current milestone — 2026-09-30

`DGB-ELECTRUM-PACKAGING-DESKTOP-INTEGRATION` — DigiByte wallet runtime,
branding, Wayland desktop integration, and self-contained AppImage packaging.

Completed so far:

- DigiByte mainnet parameters and address prefixes are defined.
- The client default network is DigiByte.
- The DigiByte electrs TCP port is `50011` (`50012` for TLS).
- POSIX client data is stored below `$HOME/.electrum-digibyte`.
- The DigiByte `servers.json` includes the public default endpoint
  `electrum-digibyte.ddns.net:50011:t`. Users can select another DigiByte
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

The DigiByte build includes `electrum-digibyte.ddns.net:50011:t` as its default
public endpoint. Users can select another DigiByte-indexing server in the
Network dialog or start the client with an explicit endpoint. If the default
server list is unavailable or empty, the GUI opens disconnected and uses the
harmless placeholder `localhost:1:s`:

```bash
./run_digibyte --digibyte -s <electrs-host>:50011:t gui
```

The AppImage accepts the same arguments:

```bash
./electrum-digibyte-4.8.2-x86_64.AppImage \
  --digibyte -s <electrs-host>:50011:t gui
```

## Development status and milestones

Development and operator testing are currently being performed on **Ubuntu 26
(x86_64/amd64)**. This project is an active DigiByte adaptation of upstream
Electrum and is not presented as an official DigiByte release.

### 2026-09-30 — Ubuntu 26 and Wayland integration

- The Wayland application identity is explicitly set to
  `electrum-digibyte`, allowing Ubuntu to associate the running wallet with
  its DigiByte dock/menu launcher.
- Docker-based AppImage build prerequisites and output instructions are
  documented below.
- These changes are pushed to the `origin/digi` branch.

### 2026-09-25 — DigiByte branding and packaging

- The GUI, wallet window, desktop entry, and Linux application icon use
  DigiByte branding instead of Bitcoin branding.
- The Lightning Channels tab is hidden because DigiByte does not support the
  Bitcoin Lightning implementation used by upstream Electrum.
- AppImage packaging bundles Python, Qt, runtime libraries, the DigiByte icon,
  and the native DigiByte PoW validator.
- The AppImage Docker builder automatically obtains the official DigiByte Core
  source and compiles the native PoW validator when it is not cached.
- A desktop-entry installer was added for source checkouts and downloaded
  AppImages.

### 2026-09-24 — wallet transaction validation

- Receiving and sending DigiByte were validated against the DigiByte-indexing
  electrs service.
- A GUI crash caused by DigiByte block heights exceeding Electrum's legacy
  three-byte UTXO ShortID field was fixed.
- Large DigiByte UTXOs now use a readable fallback identifier when the compact
  ShortID format cannot represent their height.

The AppImage build pipeline is implemented, but an AppImage file is generated
locally only when the maintainer runs the documented build command. This
repository does not claim that a binary release has already been produced.

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

Clone this DigiByte fork, not the upstream Bitcoin client:

```bash
git clone --branch digi https://github.com/digibyte-electrum/electrum-digibyte.git
cd electrum-digibyte
```

Create the virtual environment and install the runtime and DigiByte
development dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r contrib/requirements/requirements.txt
.venv/bin/pip install -r contrib/requirements/requirements-digibyte-dev.txt
```

The Qt GUI additionally requires PyQt6 and the native secp256k1 development
library. On Ubuntu 26:

```bash
sudo apt update
sudo apt install -y python3-dev python3-pyqt6 libsecp256k1-dev automake libtool
```

The native DigiByte PoW library is also required for source checkouts. Follow
the source-build instructions above; packaged applications and AppImages
already include it.

If the local environment has already been prepared, run the client with:

```bash
./run_digibyte --help
```

`run_digibyte` supplies the project-local libsecp256k1 library path and uses
the project virtual environment.

### Linux desktop icon

The Qt application and Linux desktop entry use the DigiByte-branded icon
`electrum/gui/icons/electrum_digibyte.svg`. To install the source checkout as a
user desktop application, run:

```bash
./contrib/install_desktop_entry.sh
```

For an AppImage, pass its path so the launcher points to the downloaded file:

```bash
./contrib/install_desktop_entry.sh \
  "$HOME/Downloads/electrum-digibyte-<version>-x86_64.AppImage"
```

The script installs the DigiByte icon and creates a user-level launcher under
`~/.local/share/applications`; administrator privileges are not required.

Remove the old Electrum launcher from the dock and launch **Electrum DigiByte
Wallet** once from the application menu before pinning it again. Restart the
application or log out and back in if Ubuntu's dock continues to show a cached
generic icon. AppImage builds include the same icon automatically.

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
- [x] Full header synchronization and runtime validation against the
  DigiByte-indexing electrs service.
- [x] Trusted checkpoint/header bootstrap for faster first launch, with the
  checkpoint source and header documented for independent DigiByte Core review.
- [x] Self-contained x86_64 AppImage packaging with automatic native PoW
  library compilation and bundling.
- [x] Ubuntu 26 desktop integration, DigiByte launcher/icon installation, and
  Wayland dock identity.
- [ ] Build and publish a versioned AppImage release artifact.

---

## Creating Binaries

- [Linux (tarball)](contrib/build-linux/sdist/README.md)
- [Linux (AppImage)](contrib/build-linux/appimage/README.md) — self-contained
  x86_64 bundle including Python, Qt, runtime libraries, the DigiByte icon, and
  the native DigiByte PoW validator.
- [macOS](contrib/osx/README.md)
- [Windows](contrib/build-wine/README.md)
- [Android](contrib/android/Readme.md)

### Building the AppImage from source

The AppImage build uses Docker only as an isolated, reproducible build
environment. Docker is not needed to run the finished AppImage. The builder
automatically downloads the official DigiByte Core source, compiles the native
DigiByte PoW validator, and embeds it in the AppImage. End users only download
and execute the resulting file.

The supported build target is Linux x86_64/amd64. The development environment
is Ubuntu 26.04 (`resolute`). Install Docker Engine from Docker's official APT
repository; installing only Ubuntu's base packages is not sufficient because
the `docker-ce` packages are provided by Docker's repository.

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

Allow the current user to run Docker without `sudo`, then start a new login
session. Logging out and back in is the most reliable option. On minimal
installations where `newgrp` is unavailable, install `util-linux-extra` first:

```bash
sudo usermod -aG docker "$USER"
sudo apt install -y util-linux-extra
newgrp docker
docker run --rm hello-world
```

Alternatively, close the terminal, log out of Ubuntu, log back in, and run
`docker run --rm hello-world` in a new terminal. The `docker` group grants
root-equivalent access to the host, so keep membership limited to trusted
users.

Then build from the repository root:

```bash
./contrib/build-linux/appimage/build.sh
```

The first build downloads the pinned AppImage tooling, Python sources, and the
official DigiByte Core source, so it can take time and requires internet access
and several gigabytes of temporary disk space. Subsequent builds reuse caches.
Use `ELECBUILD_NOCACHE=1` only when a clean Docker image is required. The final
file is written to `dist/electrum-digibyte-<version>-x86_64.AppImage` and can be run
without installing anything:

```bash
chmod +x dist/electrum-digibyte-*-x86_64.AppImage
./dist/electrum-digibyte-*-x86_64.AppImage
```


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
