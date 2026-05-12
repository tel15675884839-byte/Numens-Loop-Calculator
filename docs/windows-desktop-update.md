# Windows Desktop Update Contract

Loop Calculator currently targets Windows desktop distribution only. The desktop build must be a real Windows desktop shell, not the legacy `build.bat` package that starts the local FastAPI server and opens an external browser.

## Desktop Build Commands

### Recommended: Windows Installer

```bat
build-installer.bat
```

Expected output:

```text
dist-installer\LoopCalculatorSetup.exe
```

The installer:
- Copies `LoopCalculatorDesktop.exe` and `LoopCalculatorBackend.exe` into `%LOCALAPPDATA%\Programs\Loop Calculator`
- Creates a `data` directory for SQLite beside the executables
- Creates desktop and Start Menu shortcuts pointing to `LoopCalculatorDesktop.exe`
- Customers only see one shortcut and one installed program
- Does not require admin privileges (installs to user profile)

### Raw Portable Files

Use this command only when you need the unpackaged desktop files:

```bat
build-desktop.bat
```

Expected output:

```text
dist-desktop\LoopCalculatorDesktop.exe
dist-desktop\LoopCalculatorBackend.exe
```

`LoopCalculatorDesktop.exe` is the Tauri desktop window. `LoopCalculatorBackend.exe` is the bundled local FastAPI/SQLite backend sidecar. Do not ship these separately to customers.

The optional NSIS installer command is:

```bat
cd frontend
npm run desktop:installer
```

The installer command may need internet access the first time because Tauri downloads NSIS packaging tools.

Do not use `build.bat` when the requirement is an independent desktop app; that script packages `run_server.py` and opens `http://127.0.0.1:8000` in the user's browser.

## Desktop Runtime And SQLite

The desktop app uses the same FastAPI backend and SQLite storage as the Web backend, but runs it locally as a sidecar process:

```text
LoopCalculatorDesktop.exe -> starts LoopCalculatorBackend.exe -> serves http://127.0.0.1:8765
```

The frontend detects Tauri and sends API calls to:

```text
http://127.0.0.1:8765
```

The local backend stores SQLite data beside the shipped backend executable:

```text
dist-desktop\data\loop_calculator.sqlite3
```

On startup, `SQLiteStore.initialize()` creates the SQLite schema if needed and syncs built-in product records from bundled `products_db.json`. Customer-created products and projects remain local SQLite data.

## Canonical Update Addresses

Program updates and product catalog updates are separate. The manifest URLs are defined in code at:

```text
backend/app/update_config.py
```

The local backend exposes the same values at:

```text
GET /api/app/update-config
```

Expected response:

```json
{
  "platform": "windows",
  "program_update_manifest_url": "https://YOUR_DOMAIN.vercel.app/updates/windows/latest.json",
  "catalog_update_manifest_url": "https://YOUR_DOMAIN.vercel.app/updates/catalog/latest.json"
}
```

The actual manifests are served from Vercel (static files in `frontend/public/updates/`). The installer EXE is hosted on GitHub Releases. See `docs/desktop-update-flow.md` for the complete update workflow, developer release procedure, and placeholder replacement checklist.

## Program Update Manifest Shape

When program updates are implemented, publish `latest.json` at the program address with this shape:

```json
{
  "platform": "windows",
  "app_version": "1.0.0",
  "installer_url": "https://github.com/YOUR_USERNAME/YOUR_REPO/releases/download/v1.0.0/LoopCalculatorSetup.exe",
  "sha256": "replace-with-installer-sha256"
}
```

The installer is hosted on GitHub Releases, not on Vercel.

## Catalog Update Manifest Shape

When product catalog updates are implemented, publish `latest.json` at the catalog address with this shape:

```json
{
  "platform": "windows",
  "catalog_version": "2026.05.12",
  "catalog_url": "https://YOUR_DOMAIN.vercel.app/updates/catalog/products_db.json",
  "sha256": "replace-with-catalog-sha256"
}
```

The product database is hosted on Vercel alongside the manifest.

## Update Rules

- Offline startup must remain fully functional without reaching the update address.
- Online checks may run on startup or from a manual Check for Updates action.
- Program updates must verify the downloaded installer hash before prompting the user to install.
- Product catalog updates must preserve customer-created local products and only refresh built-in product records in SQLite.
- Program updates replace the desktop/backend binaries, not customer SQLite data.
- Do not add macOS or Linux update behavior until the product requirement changes.
