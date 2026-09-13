import os
import re

jsx_files = [
    'src/pages/Dashboard.jsx',
    'src/pages/Scan.jsx',
    'src/pages/Result.jsx',
    'src/pages/History.jsx',
    'src/pages/InspectionDetails.jsx',
    'src/pages/Reports.jsx',
    'src/components/Sidebar.jsx',
    'src/components/Header.jsx'
]

replacements = [
    (r"'#FFFFFF'", "'var(--text-primary)'"),
    (r"'#94A3B8'", "'var(--text-secondary)'"),
    (r"'#CBD5E1'", "'var(--text-secondary)'"),
    (r"'#64748B'", "'var(--text-muted)'"),
    (r"'#070D19'", "'var(--bg-canvas)'"),
    (r"'#050912'", "'var(--bg-canvas)'"),
    (r"'#0B132B'", "'var(--bg-canvas)'"),
    (r"'#1E2E4E'", "'var(--border-subtle)'"),
    (r"'rgba\(15, 29, 54, 0\.85\)'", "'var(--bg-card)'"),
    (r"'rgba\(15, 29, 54, 0\.7\)'", "'var(--bg-card)'"),
    (r"'rgba\(10, 17, 40, 0\.95\)'", "'var(--bg-card)'"),
    (r"'rgba\(15, 29, 54, 0\.95\)'", "'var(--bg-card)'"),
    (r"'rgba\(11, 22, 44, 0\.75\)'", "'var(--bg-card)'"),
    (r"'#0F2744'", "'var(--bg-card)'"),
    (r"'#0A192F'", "'var(--bg-canvas)'"),
    (r"'#1E293B'", "'var(--border-subtle)'"),
    (r"'#38BDF8'", "'var(--accent-primary)'"),
    (r"'#22D3EE'", "'var(--accent-primary)'"),
    (r"'#FCA5A5'", "'var(--status-noncompliant)'"),
    (r"'rgba\(6,182,212,0\.15\)'", "'var(--status-info-bg)'"),
    (r"'rgba\(6,182,212,0\.4\)'", "'var(--status-info-border)'"),
    (r"background: 'linear-gradient\(135deg, #0F2744 0%, #0A192F 100%\)'", "background: 'var(--bg-card)'"),
    (r"background: `linear-gradient\(135deg, \$\{statusBg\} 0%, rgba\(10, 17, 40, 0\.95\) 100%\)`", "background: `linear-gradient(135deg, ${statusBg} 0%, var(--bg-card) 100%)`"),
    (r"'rgba\(255, 255, 255, 0\.02\)'", "'rgba(15, 23, 42, 0.05)'"),
    (r"'rgba\(255,255,255,0\.05\)'", "'rgba(15, 23, 42, 0.05)'"),
    (r"'#F1F5F9'", "'var(--bg-canvas)'"),
    (r"'#030712'", "'var(--bg-canvas)'"),
    (r"'#1E2E4E'", "'var(--border-subtle)'"),
    (r"'rgba\(56, 189, 248, 0\.1\)'", "'var(--status-info-bg)'"),
    (r"'rgba\(56, 189, 248, 0\.25\)'", "'var(--status-info-border)'")
]

for fpath in jsx_files:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        for p, r in replacements:
            content = re.sub(p, r, content)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {fpath}')
