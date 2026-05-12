# Desktop Update Flow

This document defines the update mechanism for the Loop Calculator Windows desktop app.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Your Computer (Developer)           │
│                                                      │
│  1. Edit frontend/public/updates/*.json              │
│  2. git push → Vercel auto-deploys                  │
│  3. Upload installer to GitHub Releases              │
└─────────────────────────────────────────────────────┘
                        │
          ┌─────────────┴──────────────┐
          ▼                            ▼
┌──────────────────┐     ┌──────────────────────────┐
│  Vercel (Free)   │     │  GitHub Releases (Free)   │
│                  │     │                           │
│  updates/        │     │  LoopCalculatorSetup.exe  │
│  ├─ windows/     │     │  (up to 2GB per file)     │
│  │  └─ latest.json│    │                           │
│  └─ catalog/     │     └──────────────────────────┘
│     ├─ latest.json│
│     └─ products_db.json│
└──────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│              Customer Desktop App                    │
│                                                      │
│  Startup → check catalog → check program → done     │
└─────────────────────────────────────────────────────┘
```

## Hosting Locations

| Asset | Location | Why |
|---|---|---|
| Update manifests (JSON) | Vercel `frontend/public/updates/` | Small files, auto-deploy with frontend |
| Product database | Vercel `frontend/public/updates/catalog/` | ~14KB, well under 50MB limit |
| Installer EXE (~50MB) | GitHub Releases | No size limit (up to 2GB), free CDN |

## File Structure

```
frontend/public/updates/
├── windows/
│   └── latest.json          ← program update manifest
└── catalog/
    ├── latest.json           ← catalog update manifest
    └── products_db.json      ← full product database
```

## Update Manifest Formats

### Program Update (`updates/windows/latest.json`)

```json
{
  "platform": "windows",
  "app_version": "1.1.0",
  "installer_url": "https://github.com/YOUR_USERNAME/YOUR_REPO/releases/download/v1.1.0/LoopCalculatorSetup.exe",
  "sha256": "abc123...",
  "release_notes": "Bug fixes and new products"
}
```

Fields:
- `app_version`: Semantic version (compare with current version)
- `installer_url`: Direct download link to the new installer
- `sha256`: SHA-256 hash of the installer file for integrity verification
- `release_notes`: Human-readable change summary

### Catalog Update (`updates/catalog/latest.json`)

```json
{
  "platform": "windows",
  "catalog_version": "2026.05.12",
  "catalog_url": "https://YOUR_DOMAIN.vercel.app/updates/catalog/products_db.json",
  "sha256": "def456...",
  "release_notes": "Added 3 new detector models"
}
```

Fields:
- `catalog_version`: Date-based version (compare with current version)
- `catalog_url`: URL to download the new `products_db.json`
- `sha256`: SHA-256 hash of the products file
- `release_notes`: Human-readable change summary

## Customer Experience

### On Startup

```
1. Desktop app starts → loads local SQLite → fully offline functional
2. If online:
   a. GET /updates/catalog/latest.json
      - If catalog_version > current → prompt: "Product library has new version, sync now?"
      - Customer clicks Yes → download products_db.json → merge into SQLite
      - Merge rule: overwrite built_in=True products, preserve built_in=False products
   b. GET /updates/windows/latest.json
      - If app_version > current → prompt: "New version X.Y.Z available, download update?"
      - Customer clicks Yes → download installer → prompt to run it
3. If offline: skip both checks, app works normally
```

### Merge Rules (Catalog Update)

```python
# Pseudocode for catalog merge
local_products = sqlite.get_all_products()
remote_products = download(products_db.json)

# Keep customer-created products
customer_products = [p for p in local_products if not p.built_in]

# Replace built-in products with remote versions
built_in_products = [p for p in remote_products if p.built_in]

# Merge
sqlite.replace_all(built_in_products + customer_products)
```

## Developer Workflow

### First Time Setup

1. Replace `YOUR_DOMAIN` in these files with your Vercel domain:
   - `backend/app/update_config.py` → `VERCEL_DOMAIN`
   - `frontend/public/updates/catalog/latest.json` → `catalog_url`

2. Replace `YOUR_USERNAME/YOUR_REPO` in:
   - `frontend/public/updates/windows/latest.json` → `installer_url`

3. Deploy frontend to Vercel:
   ```bash
   cd frontend
   git push  # Vercel auto-deploys
   ```

4. Create GitHub Release and upload installer:
   ```bash
   # Tag the release
   git tag v1.0.0
   git push origin v1.0.0

   # Create release on GitHub and upload LoopCalculatorSetup.exe
   ```

### Releasing a Product Catalog Update

1. Edit `products_db.json` in project root (add/modify products)
2. Copy to public updates:
   ```bash
   copy products_db.json frontend\public\updates\catalog\products_db.json
   ```
3. Update `frontend/public/updates/catalog/latest.json`:
   - Bump `catalog_version` (use today's date: YYYY.MM.DD)
   - Update `sha256` with hash of new products_db.json
   - Update `release_notes`
4. Commit and push → Vercel auto-deploys
5. Customer's app picks up the new catalog on next startup (if online)

### Releasing a Program Update

1. Make code changes, bump version in `installer/loop-calculator.iss`
2. Build installer:
   ```bash
   build-installer.bat
   ```
3. Upload `dist-installer/LoopCalculatorSetup.exe` to GitHub Releases:
   - Create new release with tag `vX.Y.Z`
   - Upload the installer EXE
   - Compute SHA-256: `certutil -hashfile dist-installer\LoopCalculatorSetup.exe SHA256`
4. Update `frontend/public/updates/windows/latest.json`:
   - Bump `app_version`
   - Update `installer_url` to point to new GitHub release
   - Update `sha256`
   - Update `release_notes`
5. Commit and push → Vercel auto-deploys
6. Customer's app picks up the new version on next startup (if online)

## Placeholder Replacement Checklist

Before first deployment, replace these placeholders:

| Placeholder | File | Replace With |
|---|---|---|
| `YOUR_DOMAIN` | `backend/app/update_config.py` | Your Vercel domain (e.g., `loop-calculator`) |
| `YOUR_DOMAIN` | `frontend/public/updates/catalog/latest.json` | Same Vercel domain |
| `YOUR_USERNAME/YOUR_REPO` | `frontend/public/updates/windows/latest.json` | GitHub repo path |

## Backend API

The local backend exposes the update configuration at:

```
GET /api/app/update-config
```

Response:
```json
{
  "platform": "windows",
  "program_update_manifest_url": "https://YOUR_DOMAIN.vercel.app/updates/windows/latest.json",
  "catalog_update_manifest_url": "https://YOUR_DOMAIN.vercel.app/updates/catalog/latest.json"
}
```

This endpoint is used by the desktop app's update checker to know where to look for updates.

## Constraints

- Offline startup must always work without reaching any update URL
- Product catalog updates must preserve customer-created products (built_in=False)
- Program updates replace binaries, not SQLite data
- SHA-256 verification is required before installing downloaded files
- Do not add macOS or Linux update behavior until the product requirement changes
