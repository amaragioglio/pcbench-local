from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from pcbench.reports.paths import ensure_reports_dir


def save_docx_report(report: dict[str, Any], output_dir: Path | str | None = None) -> Path:
    reports_dir = ensure_reports_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"pcbench_report_{timestamp}.docx"
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
        f"Profile: {report.get('profile', 'normal')}",
        f"Started: {report.get('started_at', '')}",
        f"Finished: {report.get('finished_at', '')}",
        "",
    ]
    dashboard = report.get("dashboard")
    if dashboard:
        paragraphs.extend(
            [
                "Dashboard",
                f"Overall score: {dashboard.get('overall_score')} / 100 {dashboard.get('overall_status')}",
            ]
        )
        for row in dashboard.get("rows", []):
            paragraphs.append(f"{row['area']}: {row['score']} {row['status']} - {row['detail']}")
        paragraphs.append("")

    system = results.get("system_info")
    if system:
        paragraphs.extend(
            [
                "System",
                f"OS: {system['machine']['system']} {system['machine']['release']}",
                f"CPU: {system['cpu']['brand']}",
                f"RAM: {system['ram']['total_gib']} GiB",
                f"Local IP: {system['network'].get('local_ip') or 'Not detected'}",
                "",
            ]
        )

    memory = results.get("memory_benchmark")
    if memory:
        paragraphs.extend(
            [
                "RAM",
                f"Allocation: {memory['allocation']['status']}",
                f"Read: {memory['bandwidth']['read_mib_per_second']} MiB/s",
                f"Write: {memory['bandwidth']['write_mib_per_second']} MiB/s",
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
                f"Scaling: {cpu['score']['scaling_factor']}x",
                "",
            ]
        )

    disk = results.get("disk_benchmark")
    if disk:
        paragraphs.extend(
            [
                "Disk",
                f"Read: {disk['read']['mib_per_second']} MiB/s",
                f"Write: {disk['write']['mib_per_second']} MiB/s",
                f"Average latency: {disk['latency']['average_ms']} ms",
                "",
            ]
        )

    network = results.get("network_benchmark")
    if network:
        ping = network["ping"]
        paragraphs.extend(
            [
                "Network",
                f"Average ping: {ping.get('average_ms')} ms",
                f"Jitter: {ping.get('jitter_ms')} ms",
                f"Packet loss: {ping.get('packet_loss_percent')}%",
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
                f"Detected GPUs: {gpu.get('detected_count')}",
                f"NVIDIA: {primary.get('name', 'Unavailable')}",
                f"VRAM: {primary.get('memory_used_mib', 'N/A')} / {primary.get('memory_total_mib', 'N/A')} MiB",
                f"Temperature: {primary.get('temperature_c', 'N/A')} C",
                "",
            ]
        )

    security = results.get("security_audit")
    if security:
        summary = security["summary"]
        paragraphs.extend(
            [
                "Security",
                f"Summary: {summary['ok']} ok | {summary['warning']} warnings | {summary['info']} info",
                f"Listening ports: {len(security['listening_ports'])}",
                f"Active connections: {security['active_connections']['established_count']}",
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
