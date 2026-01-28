"""
Helper script to indent HTML Order Form sections into expanders.
This adds 4 spaces of indentation to move content inside expander blocks.
"""

# Read the file
with open('/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp/app.py', 'r') as f:
    lines = f.readlines()

# Tab 2 Section 3: Lines 4158-4441 (0-indexed: 4157-4440)
# Tab 3 Option B: Lines 5133-5415 (0-indexed: 5132-5414)

# Indent Tab 2 Section 3
for i in range(4157, 4441):  # Lines after the expander caption
    if i < len(lines):
        lines[i] = '    ' + lines[i]  # Add 4 spaces

# Indent Tab 3 Option B (adjust indices after Tab 2 changes)
# The line numbers will shift by the number of lines we modified
# But since we're just adding spaces, line count stays the same
for i in range(5132, 5415):  # Lines after the header
    if i < len(lines):
        lines[i] = '    ' + lines[i]  # Add 4 spaces

# Write back
with open('/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp/app.py', 'w') as f:
    f.writelines(lines)

print("✅ Indentation complete!")
print(f"Tab 2 Section 3: Indented lines 4158-4441")
print(f"Tab 3 Option B: Indented lines 5133-5415")
