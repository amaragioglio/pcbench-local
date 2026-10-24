# PCBench Local - Windows security posture (read-only).
# Every check is wrapped in try/catch and returns $null when it cannot run
# (missing permission, older Windows edition). Nothing here changes settings,
# and secrets such as stored passwords are never read: only their presence.
$ErrorActionPreference = 'Stop'

function Try-Get([scriptblock]$Block) { try { & $Block } catch { $null } }
function Reg([string]$Path, [string]$Name) {
  Try-Get { (Get-ItemProperty -Path $Path -Name $Name).$Name }
}

$out = [ordered]@{}

# --- Antivirus / firewall registered with Windows Security Center ---
$out.antivirus_products = Try-Get {
  @(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct |
    ForEach-Object { [ordered]@{ name = $_.displayName; state = [int]$_.productState } })
}
$out.firewall_products = Try-Get {
  @(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName FirewallProduct |
    ForEach-Object { [ordered]@{ name = $_.displayName; state = [int]$_.productState } })
}

# --- Microsoft Defender details ---
$out.defender = Try-Get {
  $s = Get-MpComputerStatus
  [ordered]@{
    antivirus_enabled = $s.AntivirusEnabled
    realtime_enabled = $s.RealTimeProtectionEnabled
    tamper_protected = $s.IsTamperProtected
    signature_age_days = $s.AntivirusSignatureAge
    quick_scan_age_days = $s.QuickScanAge
  }
}

# --- Windows Update ---
$out.last_update_days = Try-Get {
  $last = Get-HotFix | Where-Object { $_.InstalledOn } | Sort-Object InstalledOn -Descending | Select-Object -First 1
  if ($last) { [int]((Get-Date) - $last.InstalledOn).TotalDays } else { $null }
}
$out.reboot_pending = Try-Get {
  (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired') -or
  (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending')
}

# --- Account protection ---
$sys = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
$out.uac_enabled = Reg $sys 'EnableLUA'
$out.uac_admin_prompt = Reg $sys 'ConsentPromptBehaviorAdmin'
$out.guest_enabled = Try-Get { (Get-LocalUser | Where-Object { $_.SID -like '*-501' } | Select-Object -First 1).Enabled }
$winlogon = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
$out.autologon_enabled = (Reg $winlogon 'AutoAdminLogon') -eq '1'
$out.autologon_password_stored = Try-Get { $null -ne (Get-ItemProperty -Path $winlogon).PSObject.Properties['DefaultPassword'] }

# --- Remote access ---
$ts = 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server'
$out.rdp_enabled = (Reg $ts 'fDenyTSConnections') -eq 0
$out.rdp_nla = (Reg "$ts\WinStations\RDP-Tcp" 'UserAuthentication') -eq 1
$out.smb1_server = Try-Get { (Get-SmbServerConfiguration).EnableSMB1Protocol }
if ($null -eq $out.smb1_server) { $out.smb1_server = (Reg 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters' 'SMB1') -eq 1 }
$out.smb1_client = Try-Get { (Get-Service -Name mrxsmb10).StartType -ne 'Disabled' }

# --- Boot and disk protection ---
$out.secure_boot = Reg 'HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State' 'UEFISecureBootEnabled'
$out.bitlocker = Try-Get {
  $v = Get-CimInstance -Namespace root/cimv2/security/microsoftvolumeencryption -ClassName Win32_EncryptableVolume -Filter "DriveLetter='$env:SystemDrive'"
  if ($v) { [ordered]@{ protection_on = ([int]$v.ProtectionStatus -eq 1) } } else { $null }
}
$out.smartscreen = Reg 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer' 'SmartScreenEnabled'
$out.is_laptop = Try-Get { $null -ne (Get-CimInstance -ClassName Win32_Battery | Select-Object -First 1) }

$out | ConvertTo-Json -Depth 4 -Compress
