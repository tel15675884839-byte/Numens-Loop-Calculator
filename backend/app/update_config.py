from __future__ import annotations

# Deployment: Vercel (static hosting)
# The frontend build output in frontend/public/updates/ is deployed to Vercel.
# Replace YOUR_DOMAIN below with your actual Vercel domain (e.g., loop-calculator).
VERCEL_DOMAIN = "numens-loop-calculator.vercel.app"

# Product catalog update: manifest + products_db.json hosted on Vercel
WINDOWS_CATALOG_UPDATE_MANIFEST_URL = f"https://{VERCEL_DOMAIN}/updates/catalog/latest.json"

# Program update: manifest on Vercel, installer on GitHub Releases
WINDOWS_PROGRAM_UPDATE_MANIFEST_URL = f"https://{VERCEL_DOMAIN}/updates/windows/latest.json"
