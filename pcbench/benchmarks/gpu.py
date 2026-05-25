from __future__ import annotations

import subprocess
from typing import Any


BYTES_IN_MIB = 1024**2


def run_gpu_benchmark() -> dict[str, Any]:
    wmi_gpus, wmi_error = _collect_wmi_gpus()
    nvml_gpus, nvml_error = _collect_nvml_gpus()
    nvidia_smi = _collect_nvidia_smi()

    return {
        "detected_count": len(wmi_gpus) or len(nvml_gpus),
        "wmi": wmi_gpus,
        "wmi_error": wmi_error,
        "nvml": nvml_gpus,
        "nvml_error": nvml_error,
        "nvidia_smi": nvidia_smi,
        "notes": [
            "GPU inventory and driver-exposed metrics.",
            "This phase does not run a heavy graphics workload yet.",
        ],
    }


def _collect_wmi_gpus() -> tuple[list[dict[str, Any]], str | None]:
    try:
        import wmi

        connection = wmi.WMI()
        controllers = connection.Win32_VideoController()
    except Exception as error:
        return [], str(error)

    gpus: list[dict[str, Any]] = []
    for controller in controllers:
        adapter_ram = _safe_int(getattr(controller, "AdapterRAM", None))
        gpus.append(
            {
                "name": getattr(controller, "Name", None),
                "processor": getattr(controller, "VideoProcessor", None),
                "driver_version": getattr(controller, "DriverVersion", None),
                "driver_date": getattr(controller, "DriverDate", None),
                "status": getattr(controller, "Status", None),
                "adapter_ram_mib": _bytes_to_mib(adapter_ram),
                "current_horizontal_resolution": _safe_int(
                    getattr(controller, "CurrentHorizontalResolution", None)
                ),
                "current_vertical_resolution": _safe_int(
                    getattr(controller, "CurrentVerticalResolution", None)
                ),
                "current_refresh_rate": _safe_int(getattr(controller, "CurrentRefreshRate", None)),
            }
        )
    return gpus, None


def _collect_nvml_gpus() -> tuple[list[dict[str, Any]], str | None]:
    try:
        import pynvml

        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        driver = _decode(pynvml.nvmlSystemGetDriverVersion())
        gpus = []
        for index in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(index)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = _safe_nvml_call(lambda: pynvml.nvmlDeviceGetUtilizationRates(handle))
            temperature = _safe_nvml_call(lambda: pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
            gpus.append(
                {
                    "id": index,
                    "name": _decode(pynvml.nvmlDeviceGetName(handle)),
                    "driver": driver,
                    "load_percent": getattr(utilization, "gpu", None),
                    "memory_total_mib": _bytes_to_mib(memory.total),
                    "memory_used_mib": _bytes_to_mib(memory.used),
                    "memory_free_mib": _bytes_to_mib(memory.free),
                    "temperature_c": temperature,
                    "uuid": _decode(_safe_nvml_call(lambda: pynvml.nvmlDeviceGetUUID(handle))),
                }
            )
        pynvml.nvmlShutdown()
    except Exception as error:
        return [], str(error)

    return gpus, None


def _collect_nvidia_smi() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": "unavailable",
            "error": str(error),
        }

    if completed.returncode != 0:
        return {
            "status": "unavailable",
            "error": completed.stderr.strip() or completed.stdout.strip(),
        }

    rows = []
    for line in completed.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 7:
            continue
        rows.append(
            {
                "name": parts[0],
                "driver_version": parts[1],
                "memory_total_mib": _safe_int(parts[2]),
                "memory_used_mib": _safe_int(parts[3]),
                "utilization_percent": _safe_int(parts[4]),
                "temperature_c": _safe_int(parts[5]),
                "power_draw_w": _safe_float(parts[6]),
            }
        )

    return {
        "status": "passed",
        "gpus": rows,
    }


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _bytes_to_mib(value: int | None) -> int | None:
    if value is None:
        return None
    return round(value / BYTES_IN_MIB)


def _safe_nvml_call(call: Any) -> Any:
    try:
        return call()
    except Exception:
        return None


def _decode(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)
