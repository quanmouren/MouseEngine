/// Copyright (c) 2026, CIF3
/// SPDX-License-Identifier: CC BY-NC-SA 4.0
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use std::ptr;
use winapi::um::winuser::{SystemParametersInfoW, SPIF_SENDCHANGE, SPI_SETCURSORS};
use winreg::enums::*;
use winreg::RegKey;

// 光标顺序映射表
const CURSOR_ORDER_MAPPING: [&str; 15] = [
    "Arrow",
    "Help",
    "AppStarting",
    "Wait",
    "Crosshair",
    "IBeam",
    "Handwriting",
    "No",
    "SizeNS",
    "SizeWE",
    "SizeNWSE",
    "SizeNESW",
    "SizeAll",
    "Hand",
    "UpArrow",
];

/// 批量设置系统鼠标指针，写入注册表并刷新
#[pyfunction]
fn set_system_cursors(cursor_paths: Vec<Option<String>>) -> PyResult<()> {
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let base_path = r"Control Panel\Cursors";
    let (key, _) = hkcu.create_subkey(base_path)?;

    for (index, &cursor_name) in CURSOR_ORDER_MAPPING.iter().enumerate() {
        if let Some(Some(path)) = cursor_paths.get(index) {
            apply_cursor_change(&key, cursor_name, Some(path))?;
        }
    }

    refresh_system()?;
    Ok(())
}

/// 单独设置某一个系统鼠标指针
#[pyfunction]
fn set_single_cursor(name: &str, path: Option<String>) -> PyResult<()> {
    if !CURSOR_ORDER_MAPPING.contains(&name) {
        return Err(PyValueError::new_err(format!(
            "无效的光标名称 '{}'.\n有效名称列表: {:?}",
            name, CURSOR_ORDER_MAPPING
        )));
    }

    // 打开注册表
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let base_path = r"Control Panel\Cursors";
    let (key, _) = hkcu.create_subkey(base_path)?;

    // 应用更改
    apply_cursor_change(&key, name, path.as_deref())?;

    // 刷新系统
    refresh_system()?;

    Ok(())
}

/// 处理单个光标的注册表写入/删除
fn apply_cursor_change(key: &RegKey, name: &str, path: Option<&str>) -> PyResult<()> {
    match path {
        Some(p) if !p.is_empty() => {
            key.set_value(name, &p)?;
        }
        _ => {
            let _ = key.delete_value(name);
        }
    }
    Ok(())
}

/// 调用WindowsAPI刷新系统
fn refresh_system() -> PyResult<()> {
    unsafe {
        let result = SystemParametersInfoW(SPI_SETCURSORS, 0, ptr::null_mut(), SPIF_SENDCHANGE);
        if result == 0 {
            return Err(PyRuntimeError::new_err(
                "Failed to refresh system cursors (SystemParametersInfoW)",
            ));
        }
    }
    Ok(())
}

/// Python 模块入口
#[pymodule]
fn set_mouse_registry(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(set_system_cursors, m)?)?;
    m.add_function(wrap_pyfunction!(set_single_cursor, m)?)?;
    Ok(())
}