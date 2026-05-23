# PCBench Local

Herramienta de terminal para benchmark local, inventario de hardware, red, GPU y auditoria basica de seguridad.

La interfaz esta pensada para terminal: logs en vivo, barras de metricas y reportes exportables.

## Estado Actual

- CPU single-core y multi-core.
- RAM: asignacion controlada y lectura/escritura aproximada.
- Disco: lectura, escritura y latencia.
- Red: ping, jitter, DNS y conectividad TCP.
- GPU: deteccion, VRAM, uso y temperatura si el driver lo expone.
- Seguridad local: Defender, firewall, puertos, conexiones, admins e inicio automatico.
- Reportes JSON, HTML y DOCX compatible con OnlyOffice.
- Comparacion entre reportes.
- Dockerfile para uso portable, con limitaciones normales de hardware dentro de contenedores.

## Instalacion Local

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

## Uso

Ejecutar perfil normal:

```powershell
.\.venv\Scripts\python.exe main.py run
```

Perfil rapido:

```powershell
.\.venv\Scripts\python.exe main.py run --quick
```

Perfil completo:

```powershell
.\.venv\Scripts\python.exe main.py run --full
```

Comparar los dos ultimos reportes JSON:

```powershell
.\.venv\Scripts\python.exe main.py compare
```

La comparacion es mas justa cuando ambos reportes usan el mismo perfil: `quick` contra `quick`, normal contra normal o `full` contra `full`.

## Opciones

```powershell
.\.venv\Scripts\python.exe main.py run --no-save
.\.venv\Scripts\python.exe main.py run --skip-ram
.\.venv\Scripts\python.exe main.py run --skip-cpu
.\.venv\Scripts\python.exe main.py run --skip-disk
.\.venv\Scripts\python.exe main.py run --skip-network
.\.venv\Scripts\python.exe main.py run --skip-gpu
.\.venv\Scripts\python.exe main.py run --skip-security
.\.venv\Scripts\python.exe main.py run --ram-mib 2048
.\.venv\Scripts\python.exe main.py run --cpu-seconds 10
.\.venv\Scripts\python.exe main.py run --disk-mib 1024
.\.venv\Scripts\python.exe main.py run --speedtest
```

## Reportes

Cada ejecucion con guardado genera:

- `reports/pcbench_report_*.json`: datos completos para comparar.
- `reports/pcbench_report_*.html`: resumen visual en navegador.
- `reports/pcbench_report_*.docx`: documento que puedes abrir con OnlyOffice.

## Docker

Construir imagen:

```bash
docker build -t pcbench-local .
```

Ejecutar rapido:

```bash
docker run --rm -it pcbench-local
```

Guardar reportes en una carpeta local:

```bash
docker run --rm -it -v "$PWD/reports:/app/reports" pcbench-local run --quick --skip-security
```

Notas importantes de Docker:

- Un contenedor no siempre ve el hardware real igual que el host.
- Benchmarks de disco miden el filesystem montado del contenedor o volumen.
- GPU requiere configuracion extra, por ejemplo NVIDIA Container Toolkit en Linux.
- Seguridad de Windows Defender/firewall no aplica dentro de un contenedor Linux.
- Para diagnostico real de una PC Windows, es mejor correrlo localmente en Windows.

## Estructura

```text
pcbench/
  benchmarks/
    cpu.py
    disk.py
    gpu.py
    memory.py
    network.py
    system_info.py
  reports/
    compare.py
    docx_report.py
    html_report.py
    json_report.py
  security/
    audit.py
  cli.py
  runner.py
  terminal_ui.py
main.py
requirements.txt
requirements-windows.txt
Dockerfile
pyproject.toml
```

## Alcance

Esto no reemplaza herramientas profesionales como Cinebench, CrystalDiskMark, 3DMark o MemTest86. Sirve para diagnostico local, comparaciones entre ejecuciones y auditoria basica de configuracion.
