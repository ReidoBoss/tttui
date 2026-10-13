# Publishing

The workspace contains two crates:

- `tttui_core`
- `tttui`

`tttui` depends on `tttui_core`, so publish them in this order:

```sh
cargo publish -p tttui_core
cargo publish -p tttui
```

After `tttui` is published, users can install the executable globally with:

```sh
cargo install tttui
```

## Release workflow

`.github/workflows/release.yml` runs on two triggers:

- pushing a tag matching `v*`
- a manual `workflow_dispatch` with a `tag` input, which builds and attaches
  assets to an existing tag without touching crates.io. Dispatching again for a
  tag that already has a release rebuilds it and overwrites the assets.

```sh
git tag v0.1.0
git push origin v0.1.0

# attach assets to an existing tag
gh workflow run Release -f tag=v0.1.0
```

Before using the workflow, create a crates.io API token and add it to the GitHub
repository as an Actions secret named:

```text
CARGO_REGISTRY_TOKEN
```

### Release artifacts

The `build-binaries` job builds one archive per target:

| Target | Runner |
| --- | --- |
| `x86_64-unknown-linux-gnu` | `ubuntu-22.04` |
| `aarch64-unknown-linux-gnu` | `ubuntu-24.04-arm` |
| `x86_64-unknown-linux-musl` | `ubuntu-22.04` with `musl-tools` |
| `aarch64-apple-darwin` | `macos-14` |
| `x86_64-apple-darwin` | `macos-14` (cross-built) |
| `x86_64-pc-windows-msvc` | `windows-latest` |

Each archive is named `tttui-{target}.tar.gz` and contains a single leading
directory `tttui-{target}/` holding the binary, `LICENSE` and `README.md`. The
`github-release` job publishes them together with a generated `SHA256SUMS.txt`.

**This layout is a contract.** `cargo-binstall` derives asset names from the
crate's `repository` field, the full rust target triple and its own default
templates (`pkg-fmt = tgz`, filename `{name}-{target}`, binary directory
`{name}-{target}`). Because the archives follow those defaults exactly, no
`[package.metadata.binstall]` override is needed. Renaming an archive, dropping
the leading directory or switching to `.zip` or `.tar.xz` breaks `cargo
binstall`, which then falls back to a third-party build or a source compile
instead of using the release. The workflow asserts the layout before uploading.

`github-release` needs only `build-binaries`. A crates.io failure must never
cost the binaries again: on the first three tagged releases every build
succeeded and every release shipped zero assets, because attaching them was
gated behind publishing.

### Publishing order and idempotency

The `publish` job runs only for `push` events on a tag, and only in the upstream
repository: tags pushed to a fork never attempt a crates.io write, and a manual
dispatch never publishes even when it is dispatched against a tag ref, because
`workflow_dispatch` sets `github.ref` to that ref. It runs after the tag/version
check, format, check and test steps, and then:

- publishes `tttui_core`, waits until the exact version is visible on
  `index.crates.io`, and only then publishes `tttui`
- skips any version that is already on the index, so a re-run after a partial
  failure resumes instead of dying with "version already exists"

The wait polls the exact version, not the crate name. A previous version of this
job used `cargo search`, which matches as soon as the crate name exists — true
since the first release — so it never actually waited for the new version.

## Manual preflight

Before publishing, run:

```sh
cargo fmt --check
cargo check -p tttui
cargo test -p tttui
cargo package -p tttui_core
cargo package -p tttui
```

## Self-contained binaries

CI guards the release binary against build-tree paths. Bundled languages and
quotes are embedded with `include_str!`, so nothing is read from the machine
that compiled the executable. Resolving bundled content through
`env!("CARGO_MANIFEST_DIR")` bakes an absolute source path into the binary, and
the resulting release works only on the build machine: the published v2.0.0
archive panicked at startup with `index out of bounds` because no languages were
found. The guard in `.github/workflows/ci.yml` fails the build when that path,
in the form the host platform bakes, appears in the binary. It checks a stripped
copy: debug and symbol metadata can legitimately carry the same path, while the
defect lives in read-only data, which stripping keeps intact.

## Local workflow testing

GitHub Actions run on GitHub; nothing must be installed locally for them to work
after you push.

If you want a local approximation, you can install `act` and run workflows against Docker containers. Use it for quick feedback only; the GitHub-hosted run is still the real verification environment.

`actionlint` catches most workflow mistakes faster than a push.
