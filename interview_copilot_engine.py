"""
CyberSwitch 10X - Interactive Interview Prep & Technical Co-Pilot Engine (Phase 9)
Provides Gourav with verified, battle-tested KQL queries, Palo Alto PAN-OS troubleshooting steps,
Splunk SPL cheat sheets, and STAR-method interview responses tailored for 10-15 LPA GCC interviews.
"""

from typing import Dict, List, Any

KQL_CHEAT_SHEET = [
    {
        "title": "Pass-the-Hash & NTLM Brute Force Detection",
        "description": "Identifies rapid NTLM authentication failures followed by a single successful logon within 5 minutes.",
        "kql": (
            "SecurityEvent\n"
            "| where TimeGenerated >= ago(24h)\n"
            "| where EventID in (4624, 4625)\n"
            "| summarize \n"
            "    FailedAttempts = countif(EventID == 4625),\n"
            "    SuccessAttempts = countif(EventID == 4624),\n"
            "    AccountList = make_set(TargetUserName),\n"
            "    Workstations = make_set(WorkstationName)\n"
            "    by IpAddress, bin(TimeGenerated, 5m)\n"
            "| where FailedAttempts > 15 and SuccessAttempts > 0\n"
            "| project TimeGenerated, IpAddress, FailedAttempts, SuccessAttempts, AccountList, Workstations\n"
            "| order by FailedAttempts desc"
        ),
        "talking_points": "Explain how bin(TimeGenerated, 5m) windows correlate the brute-force stage to the credential compromise stage in Sentinel."
    },
    {
        "title": "Suspicious LSASS Memory Dump (Credential Harvesting)",
        "description": "Detects unauthorized access to the LSASS process (Mimikatz, Procdump, Taskmgr) using Sysmon Event ID 10 or MDE DeviceProcessEvents.",
        "kql": (
            "DeviceEvents\n"
            "| where TimeGenerated >= ago(24h)\n"
            "| where ActionType == 'OpenProcessApiCall'\n"
            "| where FileName =~ 'lsass.exe'\n"
            "| where not(InitiatingProcessFileName in~ ('MsMpEng.exe', 'csrss.exe', 'svchost.exe'))\n"
            "| where AdditionalFields contains '0x1010' or AdditionalFields contains '0x1FFFFF'\n"
            "| project TimeGenerated, DeviceName, InitiatingProcessFileName, InitiatingProcessCommandLine, AccountName\n"
            "| order by TimeGenerated desc"
        ),
        "talking_points": "Highlight access rights 0x1010 (PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ) as the hallmark signature of credential dumper tools."
    },
    {
        "title": "Suspicious Encoded PowerShell Execution (C2 / Dropper)",
        "description": "Detects base64 encoded PowerShell commands spawned by non-standard parent processes.",
        "kql": (
            "DeviceProcessEvents\n"
            "| where TimeGenerated >= ago(24h)\n"
            "| where FileName in~ ('powershell.exe', 'pwsh.exe')\n"
            "| where ProcessCommandLine has_any ('-enc', '-encodedcommand', '-e ', 'frombase64string')\n"
            "| project TimeGenerated, DeviceName, InitiatingProcessFileName, ProcessCommandLine, AccountName\n"
            "| extend DecodedCmd = base64_decode_tostring(extract(@'(?i)(?:-enc|-encodedcommand)\\s+([A-Za-z0-9+/=]+)', 1, ProcessCommandLine))\n"
            "| order by TimeGenerated desc"
        ),
        "talking_points": "Explain that Sentinel allows dynamic decoding in KQL via base64_decode_tostring() for instantaneous triage."
    },
    {
        "title": "Azure AD Impossible Travel (AITM / Token Hijacking)",
        "description": "Detects successful logons from two disparate geographic locations within an impossible physical transit window.",
        "kql": (
            "SigninLogs\n"
            "| where TimeGenerated >= ago(24h)\n"
            "| where ResultType == 0\n"
            "| project TimeGenerated, UserPrincipalName, IPAddress, Location = LocationDetails.countryOrRegion\n"
            "| serialize\n"
            "| extend PrevTime = prev(TimeGenerated), PrevLocation = prev(Location), PrevIP = prev(IPAddress), PrevUser = prev(UserPrincipalName)\n"
            "| where UserPrincipalName == PrevUser and Location != PrevLocation\n"
            "| extend TimeDiffHours = datetime_diff('hour', TimeGenerated, PrevTime)\n"
            "| where TimeDiffHours < 3 and isnotempty(Location) and isnotempty(PrevLocation)\n"
            "| project UserPrincipalName, Location, PrevLocation, IPAddress, PrevIP, TimeDiffHours"
        ),
        "talking_points": "Correlate with Conditional Access policies and token theft (Evilginx2 AITM proxy attacks)."
    }
]

PALO_ALTO_TROUBLESHOOTING = [
    {
        "topic": "Session Packet Drop & Flow Logic Inspection",
        "command": "show session id <id> | match drop\ntest security-policy-match from <zone1> to <zone2> source <ip> destination <ip> protocol <proto>",
        "key_concepts": "Palo Alto evaluates: Zone Protection -> DoS Protection -> NAT (Pre-rule lookup) -> Security Policy (First match top-down) -> App-ID -> Decryption -> Threat Prevention Profiles (AV, Anti-Spyware, Vulnerability Protection)."
    },
    {
        "topic": "SSL Forward Proxy Decryption Failure Handling",
        "command": "show system setting ssl-decrypt settings\ntest ssl-decrypt-cert host <fqdn>",
        "key_concepts": "Explain creating No-Decrypt rules with URL Category for Financial/Banking and Medical/Health traffic for regulatory compliance (PCI-DSS & GDPR), while enforcing inspection on unknown/newly registered domains."
    },
    {
        "topic": "Panorama Device Group & Template Stack Hierarchy",
        "command": "show config pushed-shared-policy\nrequest batch push ...",
        "key_concepts": "Templates control network interfaces/zones/virtual routers; Device Groups control security policies/objects. Pre-rules are pushed globally from HQ, followed by local firewall rules, followed by Post-rules."
    }
]

TOP_INTERVIEW_QUESTIONS = [
    {
        "question": "Walk me through your complete SOC L2 incident triage lifecycle for a True Positive ransomware outbreak.",
        "expected_answer_framework": "Preparation -> Detection & Analysis -> Containment -> Eradication -> Recovery -> Post-Incident Lessons Learned (NIST SP 800-61 Rev 2).",
        "star_response": (
            "\"In my role at Wipro, when a high-severity alert triggered for a suspicious Cobalt Strike beaconing pattern and Ryuk precursor artifacts, "
            "I immediately initiated the SOC L2 IR protocol. First, during Detection, I validated the alert in Microsoft Sentinel, isolating the process lineage "
            "where Word had spawned cmd.exe then PowerShell running encoded stagers. In Containment, I executed automated network containment via Defender for Endpoint (MDE) API "
            "to isolate the infected endpoints from the VLAN while keeping the MDE command channel active. At the Palo Alto firewall perimeter, "
            "I applied emergency dynamic blocklists (EDLs) via Panorama for the discovered external C2 IP addresses. In Eradication, I revoked Azure AD session tokens "
            "and forced credential resets for compromised accounts, purged persistent scheduled tasks, and reimaged affected machines. "
            "Finally, in Post-Incident, I engineered a custom Sentinel KQL analytical rule mapped to MITRE T1059.001 to prevent recurrence across the tenant.\""
        )
    },
    {
        "question": "What is the difference between Palo Alto App-ID and traditional port-based firewalls?",
        "expected_answer_framework": "Layer 7 Application identification vs Layer 4 TCP/UDP port matching.",
        "star_response": (
            "\"Traditional stateful firewalls look strictly at Layer 3/4 headers—IP and port. An attacker tunneling malicious SSH or C2 traffic through port 80/443 "
            "easily slips past traditional rules. Palo Alto App-ID examines the initial application handshake signatures and protocol decoders regardless of the port. "
            "Even if SSH or TeamViewer runs over port 443, PAN-OS identifies the application as 'ssh' or 'teamviewer' rather than 'ssl'. If the policy allows only web-browsing "
            "and ssl over 443, the session is immediately blocked with an application override or reset. This eliminates port-squatting entirely.\""
        )
    },
    {
        "question": "How do you distinguish a False Positive from a True Positive in a brute-force or privilege escalation alert?",
        "expected_answer_framework": "Context enrichment, baseline verification, authentication error codes, asset criticality.",
        "star_response": (
            "\"I begin by analyzing the specific Windows Event ID error sub-status codes. For example, in Event 4625, sub-status 0xC000006A indicates a wrong password, "
            "whereas 0xC0000064 indicates the user account doesn't even exist (external credential stuffing), and 0xC000006D indicates logon process failure. "
            "I correlate the source IP against internal SCCM/vulnerability scanners (Qualys/Tenable) to eliminate scheduled credential validation scans. "
            "Next, I check whether the failures originate from a single workstation (like an expired cached service account or Outlook password loop) or from multiple disparate IPs. "
            "Only when abnormal volume, external non-whitelisted IPs, or subsequent successful logon (0x0 / 4624) on critical tier-0 assets are present do I escalate as True Positive.\""
        )
    }
]

def get_kql_cheatsheet() -> List[Dict[str, Any]]:
    return KQL_CHEAT_SHEET

def get_palo_alto_troubleshooting() -> List[Dict[str, Any]]:
    return PALO_ALTO_TROUBLESHOOTING

def get_interview_coaching() -> List[Dict[str, Any]]:
    return TOP_INTERVIEW_QUESTIONS
