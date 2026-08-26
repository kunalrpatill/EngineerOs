import os
import re

TEMPLATE_DIR = r'C:\Users\Kunal\.gemini\antigravity\scratch\engineeros\app\templates'

replacements = [
    (r'\bbg-white\b', 'bg-body'),
    (r'\bbg-light\b', 'bg-body-secondary'),
    (r'\btext-dark\b', 'text-white')
]

for root, _, files in os.walk(TEMPLATE_DIR):
    for filename in files:
        if filename.endswith('.html'):
            filepath = os.path.join(root, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            new_content = content
            for old, new in replacements:
                new_content = re.sub(old, new, new_content)
                
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Updated {filepath}')
print('Done.')
