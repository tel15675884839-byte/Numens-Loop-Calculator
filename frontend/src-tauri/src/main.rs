#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod updater;

use std::{
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::Duration,
};
use tauri::{Emitter, Manager};

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

const BACKEND_EXE_NAME: &str = "LoopCalculatorBackend.exe";
const BACKEND_PORT: &str = "8765";
#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x08000000;

struct BackendProcess(Mutex<Option<Child>>);

fn backend_exe_path() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let app_dir = std::env::current_exe()?
        .parent()
        .ok_or("desktop executable has no parent directory")?
        .to_path_buf();
    Ok(app_dir.join(BACKEND_EXE_NAME))
}

fn spawn_backend() -> Result<Child, Box<dyn std::error::Error>> {
    let backend_path = backend_exe_path()?;
    if !backend_path.is_file() {
        return Err(format!("missing desktop backend sidecar: {}", backend_path.display()).into());
    }
    let mut command = Command::new(backend_path);
    command
        .arg("--port")
        .arg(BACKEND_PORT)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    #[cfg(target_os = "windows")]
    command.creation_flags(CREATE_NO_WINDOW);
    Ok(command.spawn()?)
}

fn stop_backend(process: &BackendProcess) {
    if let Ok(mut child) = process.0.lock() {
        if let Some(mut backend) = child.take() {
            let _ = backend.kill();
        }
    }
}

#[tauri::command]
fn get_current_version() -> String {
    updater::CURRENT_VERSION.to_string()
}

#[tauri::command]
fn check_for_updates(program_manifest_url: String, catalog_manifest_url: String) -> Result<UpdateStatus, String> {
    let mut status = UpdateStatus {
        program_update: None,
        catalog_update: None,
    };

    if let Ok(Some(manifest)) = updater::check_program_update(&program_manifest_url) {
        status.program_update = Some(format!(
            "v{} available (current: v{}). {}",
            manifest.app_version,
            updater::CURRENT_VERSION,
            manifest.release_notes.unwrap_or_default()
        ));
    }

    if let Ok(Some(manifest)) = updater::check_catalog_update(&catalog_manifest_url) {
        status.catalog_update = Some(format!(
            "Catalog {} available. {}",
            manifest.catalog_version,
            manifest.release_notes.unwrap_or_default()
        ));
    }

    Ok(status)
}

#[tauri::command]
fn apply_program_update(program_manifest_url: String) -> Result<String, String> {
    updater::check_and_apply_program_update(&program_manifest_url)?
        .ok_or_else(|| "no program update available".to_string())
}

#[tauri::command]
fn apply_catalog_update(catalog_manifest_url: String) -> Result<Vec<u8>, String> {
    let manifest = updater::check_catalog_update(&catalog_manifest_url)?
        .ok_or("no catalog update available")?;
    updater::download_catalog(&manifest)
}

#[derive(serde::Serialize)]
struct UpdateStatus {
    program_update: Option<String>,
    catalog_update: Option<String>,
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            get_current_version,
            check_for_updates,
            apply_program_update,
            apply_catalog_update,
        ])
        .setup(|app| {
            let backend = spawn_backend()?;
            *app.state::<BackendProcess>().0.lock().map_err(|_| "backend lock poisoned")? = Some(backend);
            thread::sleep(Duration::from_millis(700));

            let handle = app.handle().clone();
            thread::spawn(move || {
                thread::sleep(Duration::from_secs(3));
                let _ = check_updates_on_startup(handle);
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::CloseRequested { .. }) {
                let process = window.state::<BackendProcess>();
                stop_backend(&*process);
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Loop Calculator desktop app");
}

fn check_updates_on_startup(app: tauri::AppHandle) -> Result<(), String> {
    let port = BACKEND_PORT;
    let config_url = format!("http://127.0.0.1:{}/api/app/update-config", port);

    let mut resp = ureq::get(&config_url)
        .call()
        .map_err(|e| format!("failed to reach local backend: {e}"))?;
    let data = resp
        .body_mut()
        .read_to_vec()
        .map_err(|e| format!("failed to read update config body: {e}"))?;
    let config: serde_json::Value = serde_json::from_slice(&data)
        .map_err(|e| format!("failed to parse update config: {e}"))?;

    let program_url = config["program_update_manifest_url"]
        .as_str()
        .unwrap_or("")
        .to_string();
    let catalog_url = config["catalog_update_manifest_url"]
        .as_str()
        .unwrap_or("")
        .to_string();

    if !program_url.is_empty() {
        if let Ok(Some(_)) = updater::check_program_update(&program_url) {
            let _ = app.emit("update-available", "program");
        }
    }

    if !catalog_url.is_empty() {
        if let Ok(Some(_)) = updater::check_catalog_update(&catalog_url) {
            let _ = app.emit("catalog-update-available", ());
        }
    }

    Ok(())
}
