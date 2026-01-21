#!/usr/bin/env python3
"""
Fix CPE ETL Parser Bug: Correct platformPart, vendor, product, version extraction

The CPE URI format is: cpe:2.3:part:vendor:product:version:update:edition:...
When split by ':', the indices are:
  [0]="cpe"  [1]="2.3"  [2]=part  [3]=vendor  [4]=product  [5]=version  [6]=update...

Current bug: Indices are off by one!
  - platformPart gets vendor value (parts[3] instead of parts[2])
  - vendor gets product value (parts[4] instead of parts[3])
  - product gets version value (parts[5] instead of parts[4])
  - version gets update value (parts[6] instead of parts[5])
"""

import os
import re

def fix_cpe_etl():
    """Fix the CPE ETL parser in src/etl/etl_cpe.py"""
    
    filepath = 'E:\\DEVEL\\LAIA\\KGCS\\src\\etl\\etl_cpe.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the buggy CPE parsing code
    # Current (buggy) code:
    buggy_pattern = r'''# Parse CPE string components \(format: cpe:2\.3:part:vendor:product:version:update:edition:\.\.\.\)
    parts = cpe_name\.split\(':'\)
    if len\(parts\) >= 4:
        self\.graph\.add\(\(platform_node, SEC\.platformPart, Literal\(parts\[3\], datatype=XSD\.string\)\)\)
    if len\(parts\) >= 5:
        self\.graph\.add\(\(platform_node, SEC\.vendor, Literal\(parts\[4\], datatype=XSD\.string\)\)\)
    if len\(parts\) >= 6:
        self\.graph\.add\(\(platform_node, SEC\.product, Literal\(parts\[5\], datatype=XSD\.string\)\)\)
    if len\(parts\) >= 7 and parts\[6\] != '\*':
        self\.graph\.add\(\(platform_node, SEC\.version, Literal\(parts\[6\], datatype=XSD\.string\)\)\)'''
    
    # Fixed code:
    fixed_code = '''# Parse CPE string components (format: cpe:2.3:part:vendor:product:version:update:edition:...)
    # After split by ':', indices are: [0]="cpe" [1]="2.3" [2]=part [3]=vendor [4]=product [5]=version [6]=update...
    parts = cpe_name.split(':')
    if len(parts) >= 3:
        self.graph.add((platform_node, SEC.platformPart, Literal(parts[2], datatype=XSD.string)))
    if len(parts) >= 4:
        self.graph.add((platform_node, SEC.vendor, Literal(parts[3], datatype=XSD.string)))
    if len(parts) >= 5:
        self.graph.add((platform_node, SEC.product, Literal(parts[4], datatype=XSD.string)))
    if len(parts) >= 6 and parts[5] != '*':
        self.graph.add((platform_node, SEC.version, Literal(parts[5], datatype=XSD.string)))'''
    
    # Try regex replacement
    new_content = re.sub(buggy_pattern, fixed_code, content, flags=re.MULTILINE)
    
    if new_content != content:
        print("✓ Pattern matched and replaced via regex")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ Fixed file: {filepath}")
        return True
    
    # If regex doesn't match, try simpler string replacement with context
    # Look for the specific part-related assignments
    if 'Literal(parts[3], datatype=XSD.string)))' in content:
        print("✓ Found buggy pattern, performing manual fix...")
        
        # Replace each line individually with more context
        old1 = '''    if len(parts) >= 4:
        self.graph.add((platform_node, SEC.platformPart, Literal(parts[3], datatype=XSD.string)))
    if len(parts) >= 5:
        self.graph.add((platform_node, SEC.vendor, Literal(parts[4], datatype=XSD.string)))
    if len(parts) >= 6:
        self.graph.add((platform_node, SEC.product, Literal(parts[5], datatype=XSD.string)))
    if len(parts) >= 7 and parts[6] != '*':
        self.graph.add((platform_node, SEC.version, Literal(parts[6], datatype=XSD.string)))'''
        
        new1 = '''    if len(parts) >= 3:
        self.graph.add((platform_node, SEC.platformPart, Literal(parts[2], datatype=XSD.string)))
    if len(parts) >= 4:
        self.graph.add((platform_node, SEC.vendor, Literal(parts[3], datatype=XSD.string)))
    if len(parts) >= 5:
        self.graph.add((platform_node, SEC.product, Literal(parts[4], datatype=XSD.string)))
    if len(parts) >= 6 and parts[5] != '*':
        self.graph.add((platform_node, SEC.version, Literal(parts[5], datatype=XSD.string)))'''
        
        new_content = content.replace(old1, new1)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Fixed file: {filepath}")
            return True
    
    print("✗ Could not find pattern to fix")
    return False

if __name__ == '__main__':
    success = fix_cpe_etl()
    print(f"\nResult: {'✅ SUCCESS' if success else '❌ FAILED'}")
