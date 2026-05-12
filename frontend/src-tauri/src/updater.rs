use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::PathBuf;

pub const CURRENT_VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Deserialize)]
pub struct ProgramManifest {
    pub platform: String,
    pub app_version: String,
    pub installer_url: String,
    pub sha256: String,
    pub release_notes: Option<String>,
}

#[derive(Deserialize)]
pub struct CatalogManifest {
    pub platform: String,
    pub catalog_version: String,
    pub catalog_url: String,
    pub sha256: String,
    pub release_notes: Option<String>,
}

fn version_tuple(v: &str) -> Option<(u32, u32, u32)> {
    let parts: Vec<&str> = v.split('.').collect();
    if parts.len() != 3 {
        return None;
    }
    let major = parts[0].parse().ok()?;
    let minor = parts[1].parse().ok()?;
    let patch = parts[2].parse().ok()?;
    Some((major, minor, patch))
}

fn is_newer(remote: &str, local: &str) -> bool {
    match (version_tuple(remote), version_tuple(local)) {
        (Some(r), Some(l)) => r > l,
        _ => false,
    }
}

fn sha256_file(path: &PathBuf) -> Result<String, String> {
    let data = fs::read(path).map_err(|e| format!("failed to read file for hash: {e}"))?;
    let mut hasher = Sha256::new();
    hasher.update(&data);
    Ok(hex::encode(hasher.finalize()))
}

pub fn check_program_update(manifest_url: &str) -> Result<Option<ProgramManifest>, String> {
    let mut resp = ureq::get(manifest_url)
        .call()
        .map_err(|e| format!("failed to fetch program manifest: {e}"))?;
    let data = resp
        .body_mut()
        .read_to_vec()
        .map_err(|e| format!("failed to read program manifest body: {e}"))?;
    let manifest: ProgramManifest = serde_json::from_slice(&data)
        .map_err(|e| format!("failed to parse program manifest: {e}"))?;

    if manifest.platform != "windows" {
        return Ok(None);
    }
    if !is_newer(&manifest.app_version, CURRENT_VERSION) {
        return Ok(None);
    }
    Ok(Some(manifest))
}

pub fn download_and_install(manifest: &ProgramManifest) -> Result<(), String> {
    let temp_dir = std::env::temp_dir().join("loop-calculator-update");
    fs::create_dir_all(&temp_dir).map_err(|e| format!("failed to create temp dir: {e}"))?;

    let installer_path = temp_dir.join("LoopCalculatorSetup.exe");

    let mut resp = ureq::get(&manifest.installer_url)
        .call()
        .map_err(|e| format!("failed to download installer: {e}"))?;

    let data = resp
        .body_mut()
        .read_to_vec()
        .map_err(|e| format!("failed to read installer body: {e}"))?;

    fs::write(&installer_path, &data)
        .map_err(|e| format!("failed to write installer: {e}"))?;

    if !manifest.sha256.is_empty() && manifest.sha256 != "replace-with-sha256-of-installer" {
        let hash = sha256_file(&installer_path)?;
        if hash != manifest.sha256 {
            let _ = fs::remove_file(&installer_path);
            return Err(format!(
                "installer hash mismatch: expected {}, got {}",
                manifest.sha256, hash
            ));
        }
    }

    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        std::process::Command::new(&installer_path)
            .arg("/SILENT")
            .arg("/NORESTART")
            .creation_flags(CREATE_NO_WINDOW)
            .spawn()
            .map_err(|e| format!("failed to start installer: {e}"))?;
    }

    Ok(())
}

pub fn check_and_apply_program_update(manifest_url: &str) -> Result<Option<String>, String> {
    let manifest = check_program_update(manifest_url)?;
    match manifest {
        Some(m) => {
            download_and_install(&m)?;
            let notes = m.release_notes.unwrap_or_default();
            Ok(Some(format!(
                "v{} downloaded and installer started. {}",
                m.app_version, notes
            )))
        }
        None => Ok(None),
    }
}

pub fn check_catalog_update(manifest_url: &str) -> Result<Option<CatalogManifest>, String> {
    let mut resp = ureq::get(manifest_url)
        .call()
        .map_err(|e| format!("failed to fetch catalog manifest: {e}"))?;
    let data = resp
        .body_mut()
        .read_to_vec()
        .map_err(|e| format!("failed to read catalog manifest body: {e}"))?;
    let manifest: CatalogManifest = serde_json::from_slice(&data)
        .map_err(|e| format!("failed to parse catalog manifest: {e}"))?;

    if manifest.platform != "windows" {
        return Ok(None);
    }
    Ok(Some(manifest))
}

pub fn download_catalog(manifest: &CatalogManifest) -> Result<Vec<u8>, String> {
    let mut resp = ureq::get(&manifest.catalog_url)
        .call()
        .map_err(|e| format!("failed to download catalog: {e}"))?;

    let data = resp
        .body_mut()
        .read_to_vec()
        .map_err(|e| format!("failed to read catalog data: {e}"))?;

    if !manifest.sha256.is_empty() && manifest.sha256 != "replace-with-sha256-of-products-db" {
        let mut hasher = Sha256::new();
        hasher.update(&data);
        let hash = hex::encode(hasher.finalize());
        if hash != manifest.sha256 {
            return Err(format!(
                "catalog hash mismatch: expected {}, got {}",
                manifest.sha256, hash
            ));
        }
    }

    Ok(data)
}
