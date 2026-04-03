-- ============================================================
-- UMBRA — Demo Seed Data
-- Run AFTER 01_migration.sql
-- Supabase Dashboard → SQL Editor → Run this file
-- ============================================================

-- ============================================================
-- CLIENTS
-- ============================================================
INSERT INTO clients (id, name, industry, geography, tier) VALUES
  ('a1000000-0000-0000-0000-000000000001','Apex Financial Services','Financial Services','North America','enterprise'),
  ('a1000000-0000-0000-0000-000000000002','NovaMed Health Systems','Healthcare','Europe','enterprise'),
  ('a1000000-0000-0000-0000-000000000003','CoreGrid Energy','Energy & Utilities','North America','critical')
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- MITRE TECHNIQUES
-- ============================================================
INSERT INTO mitre_techniques (technique_id, name, tactic, parent_id, data_sources, platforms) VALUES
  ('T1059',    'Command and Scripting Interpreter','execution',NULL,
   ARRAY['process_creation','command_execution'],'{"Windows","Linux","macOS"}'),
  ('T1059.001','PowerShell','execution','T1059',
   ARRAY['process_creation','powershell_logs'],'{"Windows"}'),
  ('T1059.003','Windows Command Shell','execution','T1059',
   ARRAY['process_creation'],'{"Windows"}'),
  ('T1078',    'Valid Accounts','persistence',NULL,
   ARRAY['authentication_logs','active_directory'],'{"Windows","Linux","Cloud"}'),
  ('T1078.002','Domain Accounts','persistence','T1078',
   ARRAY['active_directory','windows_security_events'],'{"Windows"}'),
  ('T1078.004','Cloud Accounts','persistence','T1078',
   ARRAY['cloud_audit_logs','authentication_logs'],'{"Cloud"}'),
  ('T1055',    'Process Injection','privilege_escalation',NULL,
   ARRAY['process_access','edr_telemetry'],'{"Windows","Linux"}'),
  ('T1055.001','DLL Injection','privilege_escalation','T1055',
   ARRAY['process_access','module_load','edr_telemetry'],'{"Windows"}'),
  ('T1562',    'Impair Defenses','defense_evasion',NULL,
   ARRAY['windows_event_logs','edr_telemetry'],'{"Windows","Linux"}'),
  ('T1562.001','Disable or Modify Tools','defense_evasion','T1562',
   ARRAY['windows_event_logs','edr_telemetry'],'{"Windows","Linux"}'),
  ('T1562.002','Disable Windows Event Logging','defense_evasion','T1562',
   ARRAY['windows_event_logs','edr_telemetry'],'{"Windows"}'),
  ('T1003',    'OS Credential Dumping','credential_access',NULL,
   ARRAY['edr_telemetry','process_access'],'{"Windows","Linux"}'),
  ('T1003.001','LSASS Memory','credential_access','T1003',
   ARRAY['process_access','edr_telemetry','windows_security_events'],'{"Windows"}'),
  ('T1110',    'Brute Force','credential_access',NULL,
   ARRAY['authentication_logs','windows_security_events'],'{"Windows","Linux","Cloud"}'),
  ('T1021',    'Remote Services','lateral_movement',NULL,
   ARRAY['network_flow','authentication_logs'],'{"Windows","Linux"}'),
  ('T1021.001','Remote Desktop Protocol','lateral_movement','T1021',
   ARRAY['windows_security_events','network_flow','edr_telemetry'],'{"Windows"}'),
  ('T1021.006','Windows Remote Management','lateral_movement','T1021',
   ARRAY['windows_event_logs','network_flow'],'{"Windows"}'),
  ('T1041',    'Exfiltration Over C2 Channel','exfiltration',NULL,
   ARRAY['network_flow','proxy_logs'],'{"Windows","Linux","macOS"}'),
  ('T1048',    'Exfiltration Over Alternative Protocol','exfiltration',NULL,
   ARRAY['network_flow','dns_logs'],'{"Windows","Linux","Cloud"}'),
  ('T1071',    'Application Layer Protocol','command_and_control',NULL,
   ARRAY['network_flow','dns_logs','proxy_logs'],'{"Windows","Linux","Cloud"}'),
  ('T1071.001','Web Protocols','command_and_control','T1071',
   ARRAY['proxy_logs','network_flow'],'{"Windows","Linux","Cloud"}'),
  ('T1071.004','DNS','command_and_control','T1071',
   ARRAY['dns_logs','network_flow'],'{"Windows","Linux","Cloud"}'),
  ('T1566',    'Phishing','initial_access',NULL,
   ARRAY['email_gateway','edr_telemetry'],'{"Windows","Linux","macOS"}'),
  ('T1566.001','Spearphishing Attachment','initial_access','T1566',
   ARRAY['email_gateway','edr_telemetry','sandbox_logs'],'{"Windows","Linux","macOS"}'),
  ('T1486',    'Data Encrypted for Impact','impact',NULL,
   ARRAY['edr_telemetry','windows_event_logs'],'{"Windows","Linux"}')
ON CONFLICT (technique_id) DO NOTHING;

-- ============================================================
-- LOG SOURCES
-- ============================================================
INSERT INTO log_sources (id, source_key, name, category, vendor, cost_per_gb, avg_daily_gb, setup_complexity) VALUES
  ('b1000000-0000-0000-0000-000000000001','windows_security_events','Windows Security Event Logs','endpoint','Microsoft',0.35,12.5,'low'),
  ('b1000000-0000-0000-0000-000000000002','windows_event_logs','Windows Event Logs (All Channels)','endpoint','Microsoft',0.40,25.0,'low'),
  ('b1000000-0000-0000-0000-000000000003','powershell_logs','PowerShell Script Block Logging','endpoint','Microsoft',0.25,3.5,'medium'),
  ('b1000000-0000-0000-0000-000000000004','edr_telemetry','EDR Process & Memory Telemetry','endpoint','CrowdStrike',0.85,45.0,'medium'),
  ('b1000000-0000-0000-0000-000000000005','process_creation','Process Creation Events (Sysmon)','endpoint','Sysmon',0.30,8.0,'medium'),
  ('b1000000-0000-0000-0000-000000000006','active_directory','Active Directory Audit Logs','identity','Microsoft',0.30,5.0,'medium'),
  ('b1000000-0000-0000-0000-000000000007','authentication_logs','Authentication & SSO Logs','identity','Okta/Azure AD',0.20,3.0,'low'),
  ('b1000000-0000-0000-0000-000000000008','cloud_audit_logs','Cloud Control Plane Audit Logs','cloud','AWS/Azure/GCP',0.25,6.0,'medium'),
  ('b1000000-0000-0000-0000-000000000009','network_flow','Network Flow / NetFlow / IPFIX','network','Various',1.20,120.0,'high'),
  ('b1000000-0000-0000-0000-000000000010','dns_logs','DNS Query Logs','network','Infoblox',0.45,15.0,'medium'),
  ('b1000000-0000-0000-0000-000000000011','proxy_logs','Web Proxy / CASB Logs','network','Zscaler',0.55,20.0,'medium'),
  ('b1000000-0000-0000-0000-000000000012','firewall_logs','Firewall / NGFW Logs','network','Palo Alto',0.65,35.0,'medium'),
  ('b1000000-0000-0000-0000-000000000013','email_gateway','Email Gateway Logs','application','Proofpoint',0.30,4.0,'low'),
  ('b1000000-0000-0000-0000-000000000014','sandbox_logs','Sandbox/Detonation Logs','application','Any.run',0.40,1.5,'high'),
  ('b1000000-0000-0000-0000-000000000015','ssl_inspection','SSL/TLS Inspection Logs','network','Palo Alto',0.70,30.0,'high'),
  ('b1000000-0000-0000-0000-000000000016','module_load','DLL/Module Load Events (Sysmon)','endpoint','Sysmon',0.50,18.0,'medium'),
  ('b1000000-0000-0000-0000-000000000017','process_access','Process Access Events (Sysmon EID10)','endpoint','Sysmon',0.35,6.0,'medium'),
  ('b1000000-0000-0000-0000-000000000018','wmi_events','WMI Activity Logs','endpoint','Microsoft',0.20,2.0,'medium')
ON CONFLICT (source_key) DO NOTHING;

-- ============================================================
-- RULE INVENTORY
-- ============================================================
INSERT INTO rule_inventory (rule_id, name, technique_id, rule_type, severity, logic_summary) VALUES
  ('RULE-T1059-001-A','PowerShell Encoded Command Execution','T1059.001','single','high','Detects -EncodedCommand / -enc flags in PowerShell launches'),
  ('RULE-T1059-001-B','PowerShell Download Cradle Correlation','T1059.001','correlation','critical','Correlates PS Script Block with outbound network download activity'),
  ('RULE-T1059-001-C','Suspicious PowerShell Script Block Keywords','T1059.001','single','medium','Detects known malicious keywords in PS script block logs'),
  ('RULE-T1059-003-A','CMD Spawned from Office Application','T1059.003','single','high','Detects cmd.exe spawned from Word/Excel/Outlook processes'),
  ('RULE-T1059-003-B','LOLBin Execution Chain via CMD','T1059.003','chain','critical','Chain: Office → cmd.exe → LOLBin execution sequence'),
  ('RULE-T1078-002-A','Domain Account Off-Hours Login','T1078.002','single','medium','Detects domain logins outside normal business hours'),
  ('RULE-T1078-002-B','Domain Account Lateral Movement Correlation','T1078.002','correlation','high','Correlates AD auth with remote service connections'),
  ('RULE-T1078-004-A','Cloud Account Impossible Travel','T1078.004','enrichment','critical','Enriches cloud auth logs with GeoIP for impossible travel'),
  ('RULE-T1055-001-A','Remote Thread Injection into System Process','T1055.001','single','critical','Detects CreateRemoteThread targeting SYSTEM processes'),
  ('RULE-T1055-001-B','DLL Injection via Module Load Chain','T1055.001','chain','critical','Chain: process → WriteProcessMemory → CreateRemoteThread → module load'),
  ('RULE-T1562-001-A','Security Tool Process Termination','T1562.001','single','critical','Detects termination of known AV/EDR processes'),
  ('RULE-T1562-001-B','AV Registry Key Modification','T1562.001','single','high','Detects modification of antivirus product registry keys'),
  ('RULE-T1562-002-A','Windows Event Log Service Disabled','T1562.002','single','critical','Detects stop/disable of Windows EventLog service (EID 7036)'),
  ('RULE-T1003-001-A','LSASS OpenProcess with VM_READ','T1003.001','single','critical','Detects process opening LSASS with PROCESS_VM_READ rights'),
  ('RULE-T1003-001-B','Known Credential Dumper Tool Signature','T1003.001','single','critical','Detects known credential dumping tool hashes accessing LSASS'),
  ('RULE-T1003-001-C','LSASS MiniDumpWriteDump Chain','T1003.001','chain','critical','Chain: process → MiniDumpWriteDump API → .dmp file write'),
  ('RULE-T1110-A','Multiple Authentication Failures','T1110','single','medium','Detects >10 auth failures in 5 min from single source'),
  ('RULE-T1110-B','Password Spray Pattern','T1110','correlation','high','Detects spray: many users from single source OR single user many sources'),
  ('RULE-T1021-001-A','RDP from Non-Admin Workstation','T1021.001','single','high','Detects RDP originating from non-standard admin hosts'),
  ('RULE-T1021-001-B','RDP Lateral Movement Chain','T1021.001','chain','critical','Chain: compromise → credential access → RDP to critical server'),
  ('RULE-T1041-A','Large Outbound Transfer over HTTP','T1041','single','high','Detects outbound HTTP transfers >100MB to unknown destinations'),
  ('RULE-T1048-A','DNS Tunneling Detection','T1048','correlation','high','Detects high-volume encoded DNS queries for tunneling'),
  ('RULE-T1071-001-A','C2 Beaconing Pattern Detection','T1071.001','correlation','high','Detects periodic HTTP/S beaconing to external destinations'),
  ('RULE-T1071-004-A','High-Frequency DNS to Single Domain','T1071.004','single','high','Detects abnormally high DNS query rate to single domain'),
  ('RULE-T1566-001-A','Malicious Attachment Sandbox Alert','T1566.001','correlation','critical','Correlates email attachment with sandbox detonation verdict'),
  ('RULE-T1566-001-B','Office Process Spawning Shell','T1566.001','single','critical','Detects Office process spawning cmd/powershell/wscript'),
  ('RULE-T1486-A','Mass File Encryption Activity','T1486','single','critical','Detects rapid file extension changes across multiple directories')
ON CONFLICT (rule_id) DO NOTHING;

-- ============================================================
-- RULE DEPENDENCIES
-- ============================================================
INSERT INTO rule_dependencies (rule_id, source_id, dependency_type) VALUES
  -- T1059.001 rules
  ('RULE-T1059-001-A','b1000000-0000-0000-0000-000000000005','HARD'),  -- process_creation HARD
  ('RULE-T1059-001-A','b1000000-0000-0000-0000-000000000003','SOFT'),  -- powershell_logs SOFT
  ('RULE-T1059-001-B','b1000000-0000-0000-0000-000000000003','HARD'),  -- powershell_logs HARD
  ('RULE-T1059-001-B','b1000000-0000-0000-0000-000000000009','HARD'),  -- network_flow HARD
  ('RULE-T1059-001-C','b1000000-0000-0000-0000-000000000003','HARD'),  -- powershell_logs HARD
  -- T1059.003 rules
  ('RULE-T1059-003-A','b1000000-0000-0000-0000-000000000005','HARD'),
  ('RULE-T1059-003-B','b1000000-0000-0000-0000-000000000004','HARD'),  -- edr_telemetry HARD
  ('RULE-T1059-003-B','b1000000-0000-0000-0000-000000000005','HARD'),
  -- T1078 rules
  ('RULE-T1078-002-A','b1000000-0000-0000-0000-000000000006','HARD'),  -- active_directory
  ('RULE-T1078-002-A','b1000000-0000-0000-0000-000000000001','SOFT'),
  ('RULE-T1078-002-B','b1000000-0000-0000-0000-000000000006','HARD'),
  ('RULE-T1078-002-B','b1000000-0000-0000-0000-000000000009','HARD'),  -- network_flow HARD
  ('RULE-T1078-004-A','b1000000-0000-0000-0000-000000000008','HARD'),  -- cloud_audit_logs
  ('RULE-T1078-004-A','b1000000-0000-0000-0000-000000000007','HARD'),  -- authentication_logs
  -- T1055 rules
  ('RULE-T1055-001-A','b1000000-0000-0000-0000-000000000017','HARD'),  -- process_access
  ('RULE-T1055-001-A','b1000000-0000-0000-0000-000000000004','SOFT'),
  ('RULE-T1055-001-B','b1000000-0000-0000-0000-000000000017','HARD'),
  ('RULE-T1055-001-B','b1000000-0000-0000-0000-000000000016','HARD'),  -- module_load
  ('RULE-T1055-001-B','b1000000-0000-0000-0000-000000000004','HARD'),
  -- T1562 rules
  ('RULE-T1562-001-A','b1000000-0000-0000-0000-000000000004','HARD'),
  ('RULE-T1562-001-B','b1000000-0000-0000-0000-000000000002','HARD'),
  ('RULE-T1562-002-A','b1000000-0000-0000-0000-000000000002','HARD'),  -- windows_event_logs
  ('RULE-T1562-002-A','b1000000-0000-0000-0000-000000000004','SOFT'),
  -- T1003 rules
  ('RULE-T1003-001-A','b1000000-0000-0000-0000-000000000017','HARD'),  -- process_access
  ('RULE-T1003-001-A','b1000000-0000-0000-0000-000000000004','SOFT'),
  ('RULE-T1003-001-B','b1000000-0000-0000-0000-000000000004','HARD'),
  ('RULE-T1003-001-C','b1000000-0000-0000-0000-000000000017','HARD'),
  ('RULE-T1003-001-C','b1000000-0000-0000-0000-000000000004','HARD'),
  ('RULE-T1003-001-C','b1000000-0000-0000-0000-000000000001','SOFT'),
  -- T1110 rules
  ('RULE-T1110-A','b1000000-0000-0000-0000-000000000007','HARD'),
  ('RULE-T1110-B','b1000000-0000-0000-0000-000000000007','HARD'),
  ('RULE-T1110-B','b1000000-0000-0000-0000-000000000009','SOFT'),
  -- T1021 rules
  ('RULE-T1021-001-A','b1000000-0000-0000-0000-000000000001','HARD'),
  ('RULE-T1021-001-A','b1000000-0000-0000-0000-000000000009','SOFT'),
  ('RULE-T1021-001-B','b1000000-0000-0000-0000-000000000001','HARD'),
  ('RULE-T1021-001-B','b1000000-0000-0000-0000-000000000004','HARD'),
  ('RULE-T1021-001-B','b1000000-0000-0000-0000-000000000009','HARD'),  -- chain needs all 3
  -- Exfil / C2 rules
  ('RULE-T1041-A','b1000000-0000-0000-0000-000000000009','HARD'),
  ('RULE-T1041-A','b1000000-0000-0000-0000-000000000011','SOFT'),
  ('RULE-T1048-A','b1000000-0000-0000-0000-000000000010','HARD'),
  ('RULE-T1048-A','b1000000-0000-0000-0000-000000000009','SOFT'),
  ('RULE-T1071-001-A','b1000000-0000-0000-0000-000000000011','HARD'),
  ('RULE-T1071-001-A','b1000000-0000-0000-0000-000000000009','SOFT'),
  ('RULE-T1071-004-A','b1000000-0000-0000-0000-000000000010','HARD'),
  -- Phishing rules
  ('RULE-T1566-001-A','b1000000-0000-0000-0000-000000000013','HARD'),
  ('RULE-T1566-001-A','b1000000-0000-0000-0000-000000000014','HARD'),
  ('RULE-T1566-001-B','b1000000-0000-0000-0000-000000000004','HARD'),
  ('RULE-T1566-001-B','b1000000-0000-0000-0000-000000000005','HARD'),
  -- Ransomware
  ('RULE-T1486-A','b1000000-0000-0000-0000-000000000004','HARD'),
  ('RULE-T1486-A','b1000000-0000-0000-0000-000000000002','SOFT')
ON CONFLICT (rule_id, source_id) DO NOTHING;

-- ============================================================
-- CLIENT LOG SOURCES
-- Apex Financial — EDR present, process_access OFFLINE, no PS/network/DNS
-- ============================================================
INSERT INTO client_log_sources (client_id, source_id, active, ingestion_rate_gb, health) VALUES
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000001',true,14.2,'healthy'),   -- windows_security_events
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000002',true,22.0,'healthy'),   -- windows_event_logs
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000004',true,48.5,'healthy'),   -- edr_telemetry ✓
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000005',true,9.0,'healthy'),    -- process_creation ✓
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000006',true,5.5,'healthy'),    -- active_directory ✓
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000007',true,3.2,'healthy'),    -- authentication_logs ✓
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000008',true,7.0,'healthy'),    -- cloud_audit_logs ✓
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000013',true,4.1,'healthy'),    -- email_gateway ✓
  ('a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000017',false,0,'offline')      -- process_access OFFLINE → ILLUSION
  -- MISSING: powershell_logs, network_flow, dns_logs, proxy_logs, sandbox_logs, module_load
ON CONFLICT (client_id, source_id) DO NOTHING;

-- NovaMed Health — no EDR, degraded network, basic sources only
INSERT INTO client_log_sources (client_id, source_id, active, ingestion_rate_gb, health) VALUES
  ('a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000001',true,11.0,'healthy'),
  ('a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000002',true,18.0,'healthy'),
  ('a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000007',true,2.5,'healthy'),
  ('a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000006',true,4.0,'healthy'),
  ('a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000009',true,85.0,'degraded'), -- network_flow DEGRADED
  ('a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000013',true,3.0,'healthy')
  -- MISSING: edr_telemetry, process_creation, powershell_logs, dns_logs, proxy_logs, cloud_audit_logs
ON CONFLICT (client_id, source_id) DO NOTHING;

-- CoreGrid Energy — OT/ICS, minimal telemetry
INSERT INTO client_log_sources (client_id, source_id, active, ingestion_rate_gb, health) VALUES
  ('a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000001',true,8.0,'healthy'),
  ('a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000007',true,1.5,'healthy'),
  ('a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000012',true,28.0,'healthy'),  -- firewall_logs ✓
  ('a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000009',true,65.0,'healthy')   -- network_flow ✓
  -- MISSING: everything else
ON CONFLICT (client_id, source_id) DO NOTHING;

-- ============================================================
-- RULE DEPLOYMENTS (per client)
-- Apex: most rules deployed — creates maximum illusion scenario
-- ============================================================
INSERT INTO rule_deployments (client_id, rule_id, status, health, deployed_at) VALUES
  -- Apex Financial — rules deployed but sources missing = ILLUSION
  ('a1000000-0000-0000-0000-000000000001','RULE-T1059-001-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000001','RULE-T1059-001-B','deployed','healthy',NOW()), -- ILLUSION: needs powershell_logs
  ('a1000000-0000-0000-0000-000000000001','RULE-T1059-001-C','deployed','healthy',NOW()), -- ILLUSION: needs powershell_logs
  ('a1000000-0000-0000-0000-000000000001','RULE-T1059-003-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000001','RULE-T1078-002-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000001','RULE-T1078-002-B','deployed','healthy',NOW()), -- ILLUSION: needs network_flow
  ('a1000000-0000-0000-0000-000000000001','RULE-T1078-004-A','deployed','healthy',NOW()), -- BUILT: cloud+auth present
  ('a1000000-0000-0000-0000-000000000001','RULE-T1055-001-A','deployed','healthy',NOW()), -- ILLUSION: process_access offline
  ('a1000000-0000-0000-0000-000000000001','RULE-T1562-001-A','deployed','healthy',NOW()), -- BUILT: edr_telemetry present
  ('a1000000-0000-0000-0000-000000000001','RULE-T1562-001-B','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000001','RULE-T1562-002-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000001','RULE-T1003-001-A','deployed','healthy',NOW()), -- ILLUSION: process_access offline
  ('a1000000-0000-0000-0000-000000000001','RULE-T1003-001-C','deployed','healthy',NOW()), -- ILLUSION: process_access offline
  ('a1000000-0000-0000-0000-000000000001','RULE-T1110-A','deployed','healthy',NOW()),     -- BUILT: auth_logs present
  ('a1000000-0000-0000-0000-000000000001','RULE-T1110-B','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000001','RULE-T1021-001-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000001','RULE-T1021-001-B','deployed','healthy',NOW()), -- ILLUSION: network_flow missing
  ('a1000000-0000-0000-0000-000000000001','RULE-T1566-001-B','deployed','healthy',NOW()),
  -- NovaMed — minimal deployments
  ('a1000000-0000-0000-0000-000000000002','RULE-T1059-003-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000002','RULE-T1078-002-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000002','RULE-T1110-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000002','RULE-T1021-001-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000002','RULE-T1041-A','deployed','degraded',NOW()),   -- PARTIAL: degraded network
  -- CoreGrid — bare minimum
  ('a1000000-0000-0000-0000-000000000003','RULE-T1110-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000003','RULE-T1021-001-A','deployed','healthy',NOW()),
  ('a1000000-0000-0000-0000-000000000003','RULE-T1041-A','deployed','healthy',NOW())
ON CONFLICT (client_id, rule_id) DO NOTHING;

-- ============================================================
-- TECHNIQUE SCORES (Apex Financial)
-- ============================================================
INSERT INTO technique_scores (client_id, technique_id, priority_score, threat_intel_score, asset_exposure_score, industry_score, rationale) VALUES
  ('a1000000-0000-0000-0000-000000000001','T1059.001',92,88,95,90,'PowerShell weaponised in 80% of FS sector intrusions. Living-off-the-land primary TTP.'),
  ('a1000000-0000-0000-0000-000000000001','T1078.002',95,92,98,95,'Domain credential abuse #1 vector in FS. Active campaigns targeting Apex sector peers.'),
  ('a1000000-0000-0000-0000-000000000001','T1078.004',88,85,90,88,'Cloud account compromise via MFA bypass active in FS sector.'),
  ('a1000000-0000-0000-0000-000000000001','T1003.001',90,90,88,89,'LSASS dumping endemic in FS intrusions. Enables full domain compromise.'),
  ('a1000000-0000-0000-0000-000000000001','T1021.001',82,80,85,83,'RDP lateral movement standard post-exploitation path.'),
  ('a1000000-0000-0000-0000-000000000001','T1041',75,72,78,74,'HTTP exfil common. Apex handles PII + financial transaction data.'),
  ('a1000000-0000-0000-0000-000000000001','T1566.001',88,86,90,87,'Spearphishing targeting FS roles. High-volume campaigns observed Q4.'),
  ('a1000000-0000-0000-0000-000000000001','T1562.002',85,82,88,84,'Log disabling critical attacker step before exfil.'),
  ('a1000000-0000-0000-0000-000000000001','T1055.001',78,75,80,77,'Process injection used to evade EDR. Seen in Emotet/TrickBot chains.'),
  ('a1000000-0000-0000-0000-000000000001','T1110',70,68,72,69,'Brute force against VPN/OWA observed. Low-priority vs credential theft.'),
  ('a1000000-0000-0000-0000-000000000001','T1071.004',72,70,74,71,'DNS C2 used by several active groups targeting FS sector.'),
  ('a1000000-0000-0000-0000-000000000001','T1486',88,85,90,87,'Ransomware targeting FS surged 40% YoY. Apex is named-target profile.'),
  -- NovaMed scores
  ('a1000000-0000-0000-0000-000000000002','T1059.001',85,82,88,86,'PS attack chain common in healthcare ransomware campaigns.'),
  ('a1000000-0000-0000-0000-000000000002','T1078.002',90,88,92,89,'Domain credential abuse primary vector in healthcare sector.'),
  ('a1000000-0000-0000-0000-000000000002','T1003.001',88,86,90,87,'LSASS dumping precedes ransomware in 95% of healthcare incidents.'),
  ('a1000000-0000-0000-0000-000000000002','T1486',95,93,96,94,'Healthcare #1 ransomware target. Patient safety risk elevates score.'),
  -- CoreGrid scores
  ('a1000000-0000-0000-0000-000000000003','T1021.001',85,82,88,84,'RDP lateral movement from IT to OT is primary ICS attack path.'),
  ('a1000000-0000-0000-0000-000000000003','T1562.001',90,88,92,89,'AV/EDR disable standard precursor to OT-targeted attacks.'),
  ('a1000000-0000-0000-0000-000000000003','T1041',78,75,80,77,'Exfil of OT schematics and operational data high-value target.')
ON CONFLICT (client_id, technique_id) DO NOTHING;

-- ============================================================
-- DEMO HITL DECISIONS
-- ============================================================
INSERT INTO decisions (client_id, entity_type, entity_id, title, description, priority) VALUES
  ('a1000000-0000-0000-0000-000000000001','recommendation',uuid_generate_v4(),
   'Approve: Ingest Network Flow (network_flow)',
   'Resolves 7 broken rules across 6 techniques. Est. cost $4,320/month. ROI score: 89/100.',10),
  ('a1000000-0000-0000-0000-000000000001','gap',uuid_generate_v4(),
   'Review: LSASS Coverage Illusion — Critical',
   'process_access source is offline. LSASS credential dumping undetectable despite rules being deployed.',5),
  ('a1000000-0000-0000-0000-000000000001','recommendation',uuid_generate_v4(),
   'Approve: PowerShell Script Block Logging',
   '$315/month closes T1059.001 coverage illusion. Highest ROI recommendation in stack.',15),
  ('a1000000-0000-0000-0000-000000000002','gap',uuid_generate_v4(),
   'Review: No EDR Deployed — NovaMed',
   'Zero EDR telemetry at NovaMed. 8 rules require edr_telemetry (HARD). All effectively broken.',5),
  ('a1000000-0000-0000-0000-000000000003','recommendation',uuid_generate_v4(),
   'Review: CoreGrid OT Visibility — Critical Gap',
   'CoreGrid has no endpoint telemetry. T1059, T1055, T1003 are complete blind spots in OT environment.',5)
ON CONFLICT DO NOTHING;

-- ============================================================
-- VERIFY
-- ============================================================
SELECT
  'clients'        AS tbl, COUNT(*) FROM clients         UNION ALL
  SELECT 'techniques', COUNT(*) FROM mitre_techniques    UNION ALL
  SELECT 'rules',      COUNT(*) FROM rule_inventory      UNION ALL
  SELECT 'log_sources',COUNT(*) FROM log_sources         UNION ALL
  SELECT 'rule_deps',  COUNT(*) FROM rule_dependencies   UNION ALL
  SELECT 'deployments',COUNT(*) FROM rule_deployments    UNION ALL
  SELECT 'decisions',  COUNT(*) FROM decisions;
