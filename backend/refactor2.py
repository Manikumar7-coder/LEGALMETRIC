import re

with open('app/rules/compliance_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('r.status == "NEEDS_REVIEW"', 'r.status in ("NEEDS_REVIEW", "NOT_VERIFIABLE")')

def fix_sec18(match):
    block = match.group(0)
    block = block.replace('status="FAIL"', 'status="NOT_VERIFIABLE"')
    block = block.replace('in direct contravention of Section 18(1) of the Act', 'from this viewing angle. Rotate package to verify')
    return block

content = re.sub(r'if found_count == 0:.*?return RuleValidationResult\([^)]*status=\"FAIL\"[^)]*\)', fix_sec18, content, flags=re.DOTALL)

with open('app/rules/compliance_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
