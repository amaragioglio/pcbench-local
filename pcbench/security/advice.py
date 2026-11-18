"""Plain-language explanations for each security finding, in English and Spanish.

Every entry answers three questions for a non-technical person:
  title  - what we found, in one line
  why    - why it matters, without jargon
  fix    - what to do, step by step (PCBench never changes settings itself)
"""

from __future__ import annotations

from typing import Any

ADVICE: dict[str, dict[str, dict[str, Any]]] = {
    "av_ok": {
        "en": {"title": "Antivirus is on", "why": "Your PC is checking files and downloads for malware in real time.", "fix": []},
        "es": {"title": "El antivirus está activo", "why": "Tu PC revisa archivos y descargas en busca de virus en tiempo real.", "fix": []},
    },
    "av_off": {
        "en": {"title": "No active antivirus",
               "why": "Without real-time protection, a malicious download can run without being stopped.",
               "fix": ["Open Start and type Windows Security.", "Go to Virus & threat protection.",
                       "Under Virus & threat protection settings, choose Manage settings and turn on Real-time protection."]},
        "es": {"title": "No hay antivirus activo",
               "why": "Sin protección en tiempo real, una descarga maliciosa puede ejecutarse sin que nada la detenga.",
               "fix": ["Abre Inicio y escribe Seguridad de Windows.", "Entra en Protección antivirus y contra amenazas.",
                       "En Configuración, elige Administrar configuración y activa Protección en tiempo real."]},
    },
    "av_outdated": {
        "en": {"title": "Antivirus definitions are out of date",
               "why": "The antivirus only recognizes threats it has definitions for. Old definitions miss new malware.",
               "fix": ["Open Windows Security > Virus & threat protection.", "Select Protection updates > Check for updates."]},
        "es": {"title": "Las firmas del antivirus están desactualizadas",
               "why": "El antivirus solo reconoce amenazas que conoce. Con firmas viejas no detecta virus nuevos.",
               "fix": ["Abre Seguridad de Windows > Protección antivirus y contra amenazas.",
                       "Elige Actualizaciones de protección > Buscar actualizaciones."]},
    },
    "tamper_off": {
        "en": {"title": "Tamper Protection is off",
               "why": "Malware often tries to switch off your antivirus first. Tamper Protection blocks that.",
               "fix": ["Open Windows Security > Virus & threat protection > Manage settings.", "Turn on Tamper Protection."]},
        "es": {"title": "La protección contra alteraciones está apagada",
               "why": "Muchos virus intentan apagar el antivirus primero. Esta opción lo impide.",
               "fix": ["Abre Seguridad de Windows > Protección antivirus > Administrar configuración.",
                       "Activa Protección contra alteraciones."]},
    },
    "firewall_ok": {
        "en": {"title": "Firewall is on", "why": "Unwanted incoming connections are being blocked.", "fix": []},
        "es": {"title": "El firewall está activo", "why": "Se bloquean las conexiones entrantes no deseadas.", "fix": []},
    },
    "firewall_off": {
        "en": {"title": "Firewall is off for some networks",
               "why": "Other devices on the same Wi-Fi (a café, an airport) could reach services on your PC.",
               "fix": ["Open Windows Security > Firewall & network protection.",
                       "Turn on the firewall for Domain, Private and Public networks."]},
        "es": {"title": "El firewall está apagado en algunas redes",
               "why": "Otros equipos en el mismo Wi-Fi (un café, un aeropuerto) podrían conectarse a tu PC.",
               "fix": ["Abre Seguridad de Windows > Firewall y protección de red.",
                       "Activa el firewall en las redes de dominio, privada y pública."]},
    },
    "linux_firewall_off": {
        "en": {"title": "Firewall is not active",
               "why": "Services on this computer may be reachable by other devices on the network.",
               "fix": ["Ubuntu/Debian: run sudo ufw enable.", "Fedora: run sudo systemctl enable --now firewalld."]},
        "es": {"title": "El firewall no está activo",
               "why": "Los servicios de este equipo podrían ser accesibles desde otros dispositivos de la red.",
               "fix": ["Ubuntu/Debian: ejecuta sudo ufw enable.", "Fedora: ejecuta sudo systemctl enable --now firewalld."]},
    },
    "updates_old": {
        "en": {"title": "Windows has not installed updates recently",
               "why": "Most attacks use security holes that already have a fix. Updates close them.",
               "fix": ["Open Settings > Windows Update.", "Select Check for updates and install everything offered.",
                       "Restart when asked."]},
        "es": {"title": "Windows no se ha actualizado hace tiempo",
               "why": "La mayoría de los ataques usan fallas que ya tienen arreglo. Las actualizaciones las cierran.",
               "fix": ["Abre Configuración > Windows Update.", "Elige Buscar actualizaciones e instala todo.",
                       "Reinicia cuando te lo pida."]},
    },
    "updates_ok": {
        "en": {"title": "Windows is up to date", "why": "Recent security fixes are installed.", "fix": []},
        "es": {"title": "Windows está al día", "why": "Tienes instalados los arreglos de seguridad recientes.", "fix": []},
    },
    "reboot_pending": {
        "en": {"title": "A restart is pending", "why": "Some updates only take effect after restarting.",
               "fix": ["Save your work and restart the PC."]},
        "es": {"title": "Falta reiniciar", "why": "Algunas actualizaciones solo se aplican después de reiniciar.",
               "fix": ["Guarda tu trabajo y reinicia la PC."]},
    },
    "uac_off": {
        "en": {"title": "User Account Control (UAC) is off",
               "why": "Any program can make system-wide changes without asking you.",
               "fix": ["Open Start and type UAC, then open Change User Account Control settings.",
                       "Move the slider to the default level and select OK.", "Restart the PC."]},
        "es": {"title": "El Control de cuentas de usuario (UAC) está apagado",
               "why": "Cualquier programa puede hacer cambios importantes en el sistema sin preguntarte.",
               "fix": ["Abre Inicio, escribe UAC y abre Cambiar configuración de Control de cuentas de usuario.",
                       "Pon el control en el nivel predeterminado y acepta.", "Reinicia la PC."]},
    },
    "uac_silent": {
        "en": {"title": "UAC never asks before changes",
               "why": "Programs can make admin-level changes without a confirmation prompt.",
               "fix": ["Open Change User Account Control settings.", "Move the slider up to the default level."]},
        "es": {"title": "UAC nunca pide confirmación",
               "why": "Los programas pueden hacer cambios de administrador sin mostrarte un aviso.",
               "fix": ["Abre Cambiar configuración de Control de cuentas de usuario.", "Sube el control al nivel predeterminado."]},
    },
    "guest_on": {
        "en": {"title": "The Guest account is enabled",
               "why": "Anyone can sign in to this PC without a password.",
               "fix": ["Open Start, type Computer Management and open it.",
                       "Go to Local Users and Groups > Users, open Guest and check Account is disabled."]},
        "es": {"title": "La cuenta de invitado está activa",
               "why": "Cualquiera puede entrar a esta PC sin contraseña.",
               "fix": ["Abre Inicio, escribe Administración de equipos y ábrelo.",
                       "Ve a Usuarios y grupos locales > Usuarios, abre Invitado y marca La cuenta está deshabilitada."]},
    },
    "autologon_password": {
        "en": {"title": "Automatic sign-in stores your password",
               "why": "Windows keeps your password in a readable place so it can sign in for you. Any program can read it.",
               "fix": ["Press Win+R, type netplwiz and press Enter.",
                       "Check Users must enter a user name and password to use this computer and select OK."]},
        "es": {"title": "El inicio de sesión automático guarda tu contraseña",
               "why": "Windows guarda tu contraseña en un lugar legible para entrar solo. Cualquier programa podría leerla.",
               "fix": ["Presiona Win+R, escribe netplwiz y Enter.",
                       "Marca Los usuarios deben escribir su nombre y contraseña para usar el equipo y acepta."]},
    },
    "autologon_on": {
        "en": {"title": "Windows signs in automatically",
               "why": "Anyone who turns on the PC gets into your account.",
               "fix": ["Press Win+R, type netplwiz and press Enter.",
                       "Check Users must enter a user name and password to use this computer."]},
        "es": {"title": "Windows entra solo a tu cuenta",
               "why": "Cualquiera que encienda la PC entra a tu cuenta.",
               "fix": ["Presiona Win+R, escribe netplwiz y Enter.",
                       "Marca Los usuarios deben escribir su nombre y contraseña para usar el equipo."]},
    },
    "rdp_no_nla": {
        "en": {"title": "Remote Desktop is on without extra sign-in protection",
               "why": "Remote Desktop without Network Level Authentication is a frequent target of attacks.",
               "fix": ["If you do not use Remote Desktop: Settings > System > Remote Desktop > turn it off.",
                       "If you use it: on that same page, turn on Require devices to use Network Level Authentication."]},
        "es": {"title": "Escritorio remoto activo sin protección adicional",
               "why": "El Escritorio remoto sin autenticación a nivel de red es un blanco frecuente de ataques.",
               "fix": ["Si no lo usas: Configuración > Sistema > Escritorio remoto > desactívalo.",
                       "Si lo usas: en esa misma página activa Requerir autenticación a nivel de red."]},
    },
    "rdp_on": {
        "en": {"title": "Remote Desktop is on",
               "why": "Fine if you use it. If not, turning it off removes a way in.",
               "fix": ["Settings > System > Remote Desktop > turn it off if you do not need it."]},
        "es": {"title": "Escritorio remoto está activo",
               "why": "Está bien si lo usas. Si no, apagarlo quita una puerta de entrada.",
               "fix": ["Configuración > Sistema > Escritorio remoto > desactívalo si no lo necesitas."]},
    },
    "smb1_on": {
        "en": {"title": "SMBv1 file sharing is enabled",
               "why": "SMBv1 is an old, insecure protocol used by ransomware such as WannaCry.",
               "fix": ["Open Start and type Turn Windows features on or off.",
                       "Uncheck SMB 1.0/CIFS File Sharing Support and restart."]},
        "es": {"title": "SMBv1 está activado",
               "why": "SMBv1 es un protocolo viejo e inseguro que usó el ransomware WannaCry.",
               "fix": ["Abre Inicio y escribe Activar o desactivar las características de Windows.",
                       "Desmarca Compatibilidad con el protocolo para compartir archivos SMB 1.0/CIFS y reinicia."]},
    },
    "secure_boot_off": {
        "en": {"title": "Secure Boot is off",
               "why": "Secure Boot stops malicious software from loading before Windows starts.",
               "fix": ["Restart and enter your PC's UEFI/BIOS setup (often F2, F10 or Del).",
                       "Enable Secure Boot. Ask a technician if you are not sure."]},
        "es": {"title": "Arranque seguro (Secure Boot) apagado",
               "why": "El arranque seguro evita que programas maliciosos se carguen antes que Windows.",
               "fix": ["Reinicia y entra a la configuración UEFI/BIOS (suele ser F2, F10 o Supr).",
                       "Activa Secure Boot. Si no estás seguro, pídeselo a un técnico."]},
    },
    "disk_not_encrypted": {
        "en": {"title": "This laptop's disk is not encrypted",
               "why": "If the laptop is lost or stolen, anyone can read your files by removing the disk.",
               "fix": ["Open Settings > Privacy & security > Device encryption (or BitLocker on Pro editions).",
                       "Turn it on and save the recovery key somewhere safe."]},
        "es": {"title": "El disco de esta laptop no está cifrado",
               "why": "Si la pierdes o te la roban, cualquiera puede leer tus archivos sacando el disco.",
               "fix": ["Abre Configuración > Privacidad y seguridad > Cifrado de dispositivo (o BitLocker en ediciones Pro).",
                       "Actívalo y guarda la clave de recuperación en un lugar seguro."]},
    },
    "smartscreen_off": {
        "en": {"title": "SmartScreen is off", "why": "SmartScreen warns you before opening unknown or dangerous downloads.",
               "fix": ["Open Windows Security > App & browser control.", "Turn on Check apps and files."]},
        "es": {"title": "SmartScreen está apagado", "why": "SmartScreen te avisa antes de abrir descargas desconocidas o peligrosas.",
               "fix": ["Abre Seguridad de Windows > Control de aplicaciones y navegador.", "Activa Comprobar aplicaciones y archivos."]},
    },
    "ports_exposed": {
        "en": {"title": "Some services accept connections from the network",
               "why": "Usually expected (printers, sharing, dev tools). Close what you do not recognize.",
               "fix": ["Ask a technician to review the listed ports if you do not know what they are."]},
        "es": {"title": "Algunos servicios aceptan conexiones de la red",
               "why": "Suele ser normal (impresoras, compartir archivos, programas de desarrollo). Cierra lo que no reconozcas.",
               "fix": ["Si no sabes qué son los puertos listados, pide a un técnico que los revise."]},
    },
    "partial_scan": {
        "en": {"title": "Some checks need administrator rights",
               "why": "Not a problem with your PC. Running as administrator lets PCBench check everything.",
               "fix": ["Close PCBench, right-click it and choose Run as administrator."]},
        "es": {"title": "Algunas revisiones necesitan permisos de administrador",
               "why": "No es un problema de tu PC. Ejecutar como administrador permite revisar todo.",
               "fix": ["Cierra PCBench, haz clic derecho y elige Ejecutar como administrador."]},
    },
    "ports_none": {
        "en": {"title": "No common services open to the network", "why": "Nothing typical is waiting for connections from other devices.", "fix": []},
        "es": {"title": "Ningún servicio común abierto a la red", "why": "No hay servicios típicos esperando conexiones de otros equipos.", "fix": []},
    },
    "linux_sudo": {
        "en": {"title": "Some users can act as administrator", "why": "Normal on a personal computer. Make sure you recognize every account listed in the report.", "fix": []},
        "es": {"title": "Algunos usuarios pueden actuar como administrador", "why": "Es normal en una PC personal. Revisa que reconozcas todas las cuentas del reporte.", "fix": []},
    },
    "linux_sudo_none": {
        "en": {"title": "No extra administrator accounts", "why": "Only the system can make administrative changes.", "fix": []},
        "es": {"title": "Sin cuentas de administrador extra", "why": "Solo el sistema puede hacer cambios de administrador.", "fix": []},
    },
    "linux_services": {
        "en": {"title": "Background services listed", "why": "For a technician: the report includes the active services.", "fix": []},
        "es": {"title": "Servicios en segundo plano listados", "why": "Para un técnico: el reporte incluye los servicios activos.", "fix": []},
    },
    "linux_services_unknown": {
        "en": {"title": "Background services could not be read", "why": "This system does not expose them; not a problem by itself.", "fix": []},
        "es": {"title": "No se pudieron leer los servicios en segundo plano", "why": "Este sistema no los expone; no es un problema en sí.", "fix": []},
    },
    "linux_firewall_unknown": {
        "en": {"title": "Could not tell whether a firewall is active", "why": "No known firewall tool answered.", "fix": []},
        "es": {"title": "No se pudo saber si hay firewall activo", "why": "Ninguna herramienta de firewall conocida respondió.", "fix": []},
    },
    "container": {
        "en": {"title": "Running inside a container or WSL", "why": "Hardware and security results describe the container, not the real PC.", "fix": []},
        "es": {"title": "Se está ejecutando dentro de un contenedor o WSL", "why": "Los resultados describen el contenedor, no la PC real.", "fix": []},
    },
    "many_admins": {
        "en": {"title": "Several administrator accounts", "why": "Each administrator account is another way in. Remove the ones nobody uses.", "fix": []},
        "es": {"title": "Varias cuentas de administrador", "why": "Cada cuenta de administrador es otra puerta de entrada. Quita las que nadie usa.", "fix": []},
    },
}


def advice_for(finding: dict[str, Any], language: str = "en") -> dict[str, Any]:
    """Title, explanation and fix steps for a finding, falling back to its raw message."""
    entry = ADVICE.get(str(finding.get("id", "")), {})
    text = entry.get(language) or entry.get("en")
    if text:
        return text
    return {"title": f"{finding.get('area', '')}: {finding.get('message', '')}", "why": "", "fix": []}
