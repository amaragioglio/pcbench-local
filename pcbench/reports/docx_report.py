from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


REPORTS_DIR = Path("reports")


def save_docx_report(report: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"pcbench_report_{timestamp}.docx"
    paragraphs = _build_paragraphs(report)
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types())
        archive.writestr("_rels/.rels", _rels())
        archive.writestr("word/document.xml", _document_xml(paragraphs))
    return path


def _build_paragraphs(report: dict[str, Any]) -> list[str]:
    results = report.get("results", {})
    paragraphs = [
        "PCBench Local Report",
        f"Perfil: {report.get('profile', 'normal')}",
        f"Inicio: {report.get('started_at', '')}",
        f"Fin: {report.get('finished_at', '')}",
        "",
    ]
    dashboard = report.get("dashboard")
    if dashboard:
        paragraphs.extend(
            [
                "Dashboard",
                f"Score general: {dashboard.get('overall_score')} / 100 {dashboard.get('overall_status')}",
            ]
        )
        for row in dashboard.get("rows", []):
            paragraphs.append(f"{row['area']}: {row['score']} {row['status']} - {row['detail']}")
        paragraphs.append("")

    system = results.get("system_info")
    if system:
        paragraphs.extend(
            [
                "Sistema",
                f"OS: {system['machine']['system']} {system['machine']['release']}",
                f"CPU: {system['cpu']['brand']}",
                f"RAM: {system['ram']['total_gib']} GiB",
                f"IP local: {system['network'].get('local_ip') or 'No detectada'}",
                "",
            ]
        )

    memory = results.get("memory_benchmark")
    if memory:
        paragraphs.extend(
            [
                "RAM",
                f"Asignacion: {memory['allocation']['status']}",
                f"Lectura: {memory['bandwidth']['read_mib_per_second']} MiB/s",
                f"Escritura: {memory['bandwidth']['write_mib_per_second']} MiB/s",
                "",
            ]
        )

    cpu = results.get("cpu_benchmark")
    if cpu:
        paragraphs.extend(
            [
                "CPU",
                f"Single-core: {cpu['score']['single_core']} pts",
                f"Multi-core: {cpu['score']['multi_core']} pts",
                f"Escalado: {cpu['score']['scaling_factor']}x",
                "",
            ]
        )

    disk = results.get("disk_benchmark")
    if disk:
        paragraphs.extend(
            [
                "Disco",
                f"Lectura: {disk['read']['mib_per_second']} MiB/s",
                f"Escritura: {disk['write']['mib_per_second']} MiB/s",
                f"Latencia media: {disk['latency']['average_ms']} ms",
                "",
            ]
        )

    network = results.get("network_benchmark")
    if network:
        ping = network["ping"]
        paragraphs.extend(
            [
                "Red",
                f"Ping medio: {ping.get('average_ms')} ms",
                f"Jitter: {ping.get('jitter_ms')} ms",
                f"Perdida de paquetes: {ping.get('packet_loss_percent')}%",
                "",
            ]
        )

    gpu = results.get("gpu_benchmark")
    if gpu:
        nvidia = gpu.get("nvidia_smi", {})
        primary = nvidia.get("gpus", [{}])[0] if nvidia.get("gpus") else {}
        paragraphs.extend(
            [
                "GPU",
                f"GPUs detectadas: {gpu.get('detected_count')}",
                f"NVIDIA: {primary.get('name', 'No disponible')}",
                f"VRAM: {primary.get('memory_used_mib', 'N/A')} / {primary.get('memory_total_mib', 'N/A')} MiB",
                f"Temperatura: {primary.get('temperature_c', 'N/A')} C",
                "",
            ]
        )

    security = results.get("security_audit")
    if security:
        summary = security["summary"]
        paragraphs.extend(
            [
                "Seguridad",
                f"Resumen: {summary['ok']} ok | {summary['warning']} warnings | {summary['info']} info",
                f"Puertos escucha: {len(security['listening_ports'])}",
                f"Conexiones activas: {security['active_connections']['established_count']}",
            ]
        )

    return paragraphs


def _document_xml(paragraphs: list[str]) -> str:
    body = "".join(_paragraph(text) for text in paragraphs)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body}
    <w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
  </w:body>
</w:document>"""


def _paragraph(text: str) -> str:
    return f"<w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p>"


def _content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""


def _rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
