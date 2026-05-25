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
- Seguridad Linux: firewall basico, sudo users, puertos, conexiones, servicios systemd y deteccion de contenedor.
- Reportes JSON, HTML y DOCX compatible con OnlyOffice.
- Reporte Markdown para GitHub/issues.
- Dashboard con score general y estado por categoria.
- Comparacion entre reportes.
- Dockerfile para uso portable, con limitaciones normales de hardware dentro de contenedores.

## Seguridad del Proyecto

- Los reportes locales se guardan en `/reports/` y no se suben a Git.
- La auditoria de seguridad es de solo lectura.
- No hay subida automatica de datos.
- Usa `--sanitize` para guardar reportes compartibles sin hostnames, IPs, usuarios o comandos en claro.
- Si no ejecutas como administrador/root, la auditoria marca `partial: true` porque algunos datos pueden estar limitados.
- La ejecucion deja trazabilidad local en `reports/pcbench.log`, tambien ignorado por Git.
- Ver [SECURITY.md](SECURITY.md) para reglas y alcance.

## Instalacion Local

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
```

Desarrollo en Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

## Uso

Modo interactivo recomendado:

```powershell
.\.venv\Scripts\python.exe main.py wizard
```

En Windows tambien puedes ejecutar:

```powershell
.\pcbench.bat
```

El wizard incluye presets:

- `quick`: Recon rapido con CPU/RAM/DISCO y reportes ligeros.
- `full`: Diagnostico completo con todos los modulos.
- `supabase`: Core benchmark + JSON optimizado para Supabase.
- `custom`: seleccion manual de perfil, modulos y reportes.

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

Comparar solo reportes del mismo perfil:

```powershell
.\.venv\Scripts\python.exe main.py compare --profile quick
```

Comparar archivos especificos:

```powershell
.\.venv\Scripts\python.exe main.py compare --base reports\old.json --current reports\new.json
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
.\.venv\Scripts\python.exe main.py run --reports json,html,supabase
.\.venv\Scripts\python.exe main.py run --sanitize --reports json,html,supabase
```

## Reportes

Cada ejecucion con guardado genera:

- `reports/pcbench_report_*.json`: datos completos para comparar.
- `reports/pcbench_report_*.html`: resumen visual en navegador.
- `reports/pcbench_report_*.docx`: documento que puedes abrir con OnlyOffice.
- `reports/pcbench_report_*.md`: resumen Markdown para GitHub.
- `reports/pcbench_supabase_*.json`: payload con tablas planas para Supabase.

### JSON para Supabase

El export Supabase genera un JSON con estas claves:

- `pcbench_runs`
- `pcbench_metrics`
- `pcbench_findings`

Cada clave contiene una lista de filas pensadas para importar o insertar en tablas de Supabase.

Si vas a compartir o subir reportes fuera de tu PC, ejecuta con `--sanitize`. El benchmark se calcula igual, pero los archivos guardados reemplazan hostnames, IPs, usuarios, comandos y endpoints por tokens hash truncados.

## Docker

Construir imagen:

```powershell
docker build -t pcbench-local .
```

Ejecutar rapido:

```powershell
docker run --rm -it pcbench-local
```

Guardar reportes en una carpeta local:

PowerShell:

```powershell
docker run --rm -it -v ${PWD}\reports:/app/reports pcbench-local run --quick --skip-security
```

Bash:

```bash
docker run --rm -it -v "$PWD/reports:/app/reports" pcbench-local run --quick --skip-security
```

Si tu terminal no soporta TTY, ejecuta sin `-it`:

```powershell
docker run --rm pcbench-local
```

Validado en Docker Desktop con Linux containers:

- `docker build -t pcbench-local .`
- `docker run --rm pcbench-local`
- `docker run --rm -v <ruta-local>/reports:/app/reports pcbench-local run --quick --skip-security --skip-gpu --skip-network`

Notas importantes de Docker:

- Un contenedor no siempre ve el hardware real igual que el host.
- Benchmarks de disco miden el filesystem montado del contenedor o volumen.
- GPU requiere configuracion extra, por ejemplo NVIDIA Container Toolkit en Linux.
- Seguridad de Windows Defender/firewall no aplica dentro de un contenedor Linux.
- En Linux/Docker se usa auditoria Linux de solo lectura.
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
    markdown_report.py
    metrics.py
  security/
    audit.py
  cli.py
  runner.py
  terminal_ui.py
main.py
pcbench.bat
requirements.txt
requirements-dev.txt
requirements-windows.txt
Dockerfile
pyproject.toml
```

## Alcance

Esto no reemplaza herramientas profesionales como Cinebench, CrystalDiskMark, 3DMark o MemTest86. Sirve para diagnostico local, comparaciones entre ejecuciones y auditoria basica de configuracion.
