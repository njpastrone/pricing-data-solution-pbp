"""
Script to indent all content after line 357 (inside with tab2:) by 4 spaces
This ensures all existing workflow content is properly inside Tab 2
"""

def indent_content_after_line(filename, start_line_num):
    """Indent all lines after start_line_num by 4 spaces"""
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Indent lines after start_line_num
    for i in range(start_line_num, len(lines)):
        # Don't indent empty lines
        if lines[i].strip():
            lines[i] = '    ' + lines[i]

    # Write back
    with open(filename, 'w') as f:
        f.writelines(lines)

    print(f"Indented {len(lines) - start_line_num} lines starting from line {start_line_num + 1}")

if __name__ == "__main__":
    indent_content_after_line('app.py', 357)  # Line 358 onwards (0-indexed: 357)
