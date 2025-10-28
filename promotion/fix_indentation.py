#!/usr/bin/env python3

import re

def fix_indentation():
    """Fix indentation issues in promotion.py"""
    
    # Read the file
    with open('promotion/doctype/promotion/promotion.py', 'r') as f:
        lines = f.readlines()
    
    # Fix common indentation patterns
    fixed_lines = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Fix lines with too many tabs
        if line.startswith('\t\t\t\t\t\t\t'):
            line = line.replace('\t\t\t\t\t\t\t', '\t\t\t\t\t\t', 1)
        elif line.startswith('\t\t\t\t\t\t'):
            line = line.replace('\t\t\t\t\t\t', '\t\t\t\t\t', 1)
        
        # Fix specific problematic lines
        if line_num == 131:
            line = re.sub(r'^\t\t\t\t\t', '\t\t\t\t', line)
        elif line_num == 149:
            line = re.sub(r'^\t\t\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 183:
            line = re.sub(r'^\t\t\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 215:
            line = re.sub(r'^\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 222:
            line = re.sub(r'^\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 228:
            line = re.sub(r'^\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 238:
            line = re.sub(r'^\t\t\t\t', '\t\t\t\t\t\t', line)
        elif line_num == 287:
            line = re.sub(r'^\t\t\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 362:
            line = re.sub(r'^\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 369:
            line = re.sub(r'^\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 371:
            line = re.sub(r'^\t\t\t\t', '\t\t\t\t\t', line)
        elif line_num == 373:
            line = re.sub(r'^\t\t\t\t', '\t\t\t\t\t', line)
        
        fixed_lines.append(line)
    
    # Write back the fixed content
    with open('promotion/doctype/promotion/promotion.py', 'w') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation issues")

if __name__ == "__main__":
    fix_indentation()


