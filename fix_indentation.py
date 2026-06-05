import re

def fix_indentation(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace tabs with 4 spaces
    content = content.replace('\t', '    ')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed indentation in {filepath}")

# Fix your news.py file
fix_indentation('app/services/news.py')
print("✅ Done! Now run: git add . && git commit -m 'fix indentation' && git push origin main")