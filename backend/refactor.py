import re

with open('app/rules/compliance_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("f_info.get('status') == 'Low Confidence'", "f_info.get('status') == 'OCR_UNCERTAIN'")
content = content.replace('f_info.get("status") == "Low Confidence"', 'f_info.get("status") == "OCR_UNCERTAIN"')
content = content.replace('f_info.get("status") == "NOT_VERIFIABLE"', 'f_info.get("status") in ["NOT_VERIFIABLE", "Missing"]')

def fix_missing(match):
    block = match.group(0)
    block = block.replace('status="FAIL"', 'status="NOT_VERIFIABLE"')
    block = block.replace("status='FAIL'", "status='NOT_VERIFIABLE'")
    block = block.replace("missing from the package label", "not verifiable from the provided image")
    return block

content = re.sub(r'if not val:.*?return RuleValidationResult\([^\)]*status=[\"\']FAIL[\"\'][^\)]*\)', fix_missing, content, flags=re.DOTALL)

with open('app/rules/compliance_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
