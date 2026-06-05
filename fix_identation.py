import re

def fix_indentation(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        # Replace tabs with 4 spaces
        new_line = line.replace('\t', '    ')
        new_lines.append(new_line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Fixed indentation in {filepath}")

# Fix your news.py file
fix_indentation('app/services/news.py')
print("Done! Now commit and push the changes.")