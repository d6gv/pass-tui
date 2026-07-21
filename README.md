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

On startup pass-tui checks for an active `pass-cli` session. If there is
none, it shows the login screen; otherwise it lands on the vault list. From
there you can browse vaults, filter and open items, view an item's fields
(secrets masked), copy a field to the clipboard, and create, edit, or delete
items.

Keyboard shortcuts (also shown in the footer, and under `?`):

| Key      | Where        | Action                                   |
| -------- | ------------ | ---------------------------------------- |
| `l`      | Login        | Log in (hands off to pass-cli)           |
| `↑` `↓`  | Lists        | Move between rows                         |
| `enter`  | Vault list   | Open the selected vault                  |
| `enter`  | Item list    | Open the selected item                   |
| `/`      | Item list    | Focus the live title filter              |
| `n`      | Item list    | New item (login / note / card)           |
| `r`      | Lists        | Reload from pass-cli                      |
| `v`      | Item detail  | Reveal / hide sensitive fields           |
| `c`      | Item detail  | Copy the selected field (auto-clears)    |
| `e`      | Item detail  | Edit the item                            |
| `d`      | Item detail  | Delete the item (with confirmation)      |
| `ctrl+s` | Forms        | Save                                     |
| `s`      | Vault list   | Open settings                            |
| `ctrl+l` | Vault list   | Log out                                  |
| `esc`    | Pushed view  | Go back / cancel                         |
| `?`      | Anywhere     | Toggle the help overlay                  |
| `ctrl+c` | Anywhere     | Quit                                     |

Copied secrets are cleared from the clipboard automatically after a
configurable timeout, with a countdown shown in the item detail view.

A pass-cli failure (e.g. no network) is shown in a dismissable error modal
rather than crashing the app.

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
  app.py              # main Textual App: session routing, clipboard, navigation
  password.py         # client-side password generation (secrets)
  cli/                # invokes pass-cli and parses its JSON output
    runner.py         # run_pass_cli(*args) -> dict | list, raises PassCliError
    auth.py           # SessionInfo, fetch_session(), logout()
    vault.py          # Vault model and list_vaults()
    item.py           # Item/ItemDetail models, list/get/create/update/delete
  screens/            # Textual screens
    base.py           # shared header/footer chrome (ChromeScreen, BackScreen)
    login.py          # login screen
    vault_list.py     # vault list (landing screen once logged in)
    item_list.py      # items in a vault, with live filter
    item_detail.py    # item fields, masking, copy, edit/delete entry points
    forms.py          # login/note/card create & edit forms + validation
    new_item.py       # "which item type?" chooser modal
    confirm.py        # double-confirmation delete modal
    settings.py       # settings (skeleton)
    help.py           # help overlay (?)
    error.py          # non-fatal error modal
  widgets/            # reusable custom widgets
    password_generator.py
tests/                # pytest + Textual Pilot; pass-cli is always mocked
```

`config.py` (config file handling) will be added in a later phase.

## License

See [LICENSE](LICENSE).
