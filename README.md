# pass-tui

A terminal UI (TUI) for [Proton Pass](https://proton.me/pass), built with
[Textual](https://textual.textualize.io/).

pass-tui does **not** reimplement Proton's end-to-end encryption or SRP
authentication. It is a presentation layer over the official
[`pass-cli`](https://github.com/protonpass/pass-cli) binary: it invokes
`pass-cli` as a subprocess and parses its JSON output (`--output json`).
Secure session storage (system keyring, `PROTON_PASS_KEY_PROVIDER`, etc.) is
handled entirely by `pass-cli` — pass-tui never touches it.

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** for dependency management
- **`pass-cli`**, installed and on your `PATH`. Follow the install
  instructions at <https://github.com/protonpass/pass-cli>, then verify:

  ```sh
  pass-cli --version
  ```

  You do not need to be logged in to launch the app, but you will need an
  active session (`pass-cli login`) to read your vaults.

## Setup

Clone the repository and install dependencies (including the dev group):

```sh
git clone https://github.com/danielgimvil/pass-tui.git
cd pass-tui
uv sync
```

`uv sync` creates a virtual environment in `.venv/` and installs everything
pinned in `uv.lock`.

## Running

```sh
uv run pass-tui
```

While the app is running:

- `ctrl+d` — hidden debug command: dumps the JSON of `pass-cli info` (or a
  readable error if `pass-cli` is missing or you are not logged in) through
  the runner. Useful for confirming the CLI wiring works.
- `ctrl+c` — quit.

## Development

Run the app with Textual's dev mode (console + hot-reload):

```sh
uv run textual run --dev pass_tui.app:PassTuiApp
```

In a second terminal, open the Textual dev console to see logs:

```sh
uv run textual console
```

Quality checks:

```sh
uv run pytest        # tests (subprocess is mocked; no Proton account needed)
uv run ruff check .  # lint
uv run ruff format . # format
uv run mypy .        # type-check (strict)
```

## Project layout

```
src/pass_tui/
  app.py            # main Textual App
  cli/              # invokes pass-cli and parses its JSON output
    runner.py       # run_pass_cli(*args) -> dict | list, raises PassCliError
  screens/          # Textual screens (added in later phases)
  widgets/          # reusable custom widgets (added in later phases)
  config.py         # config file handling (added in later phases)
tests/
```

## License

See [LICENSE](LICENSE).
