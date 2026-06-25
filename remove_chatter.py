import os, re

views_dir = r'c:\Users\DELL\Desktop\odoo\custom-addons\funeral_assurance\views'
for f in os.listdir(views_dir):
    if f.endswith('.xml'):
        filepath = os.path.join(views_dir, f)
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove the oe_chatter div and its contents
        new_content = re.sub(r'\s*<div class="oe_chatter">.*?</div>', '', content, flags=re.DOTALL)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Cleaned {f}")
