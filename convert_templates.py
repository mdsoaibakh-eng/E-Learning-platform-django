import os
import re

TEMPLATE_DIR = r"lms/templates/lms"

def convert_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # 1. {% extends "base.html" %} -> {% extends "lms/base.html" %}
    content = re.sub(r'{%\s*extends\s+["\']base\.html["\']\s*%}', '{% extends "lms/base.html" %}', content)
    
    # 2. url_for('static', filename='...') -> {% static '...' %}
    # Need to ensure {% load static %} is present if static is used.
    if "url_for('static'" in content or 'url_for("static"' in content:
        if "{% load static %}" not in content:
            # Insert at top, but after extends if present
            if "{% extends" in content:
                content = re.sub(r'({%\s*extends.*?%})', r'\1\n{% load static %}', content, count=1)
            else:
                content = "{% load static %}\n" + content
    
    content = re.sub(r"\{\{\s*url_for\('static',\s*filename=['\"](.*?)['\"]\)\s*\}\}", r"{% static '\1' %}", content)
    content = re.sub(r"\{\{\s*url_for\(\"static\",\s*filename=['\"](.*?)['\"]\)\s*\}\}", r"{% static '\1' %}", content)

    # 3. url_for('view', arg=val) -> {% url 'view' arg=val %}
    # This is tricky because of nested parens and args.
    # Simple case: {{ url_for('index') }}
    content = re.sub(r"\{\{\s*url_for\('(\w+)'\)\s*\}\}", r"{% url '\1' %}", content)
    
    # Case with args: {{ url_for('detail', course_id=course.id) }}
    # Regex to capture view name and args
    def replace_url_args(match):
        view_name = match.group(1)
        args_str = match.group(2)
        # simplistic parsing of args: key=value
        # Django supports key=value. 
        # But Flask might have multiple.
        # We just keep the args string as is, removing parens usually works if syntax is compatible.
        # But Flask: course_id=course.id. Django: course_id=course.id. COMPATIBLE.
        return f"{{% url '{view_name}' {args_str} %}}"

    content = re.sub(r"\{\{\s*url_for\('(\w+)',\s*(.*?)\)\s*\}\}", replace_url_args, content)
    
    # 4. Session access: session['key'] or session.get('key')
    # Django template: request.session.key
    # CAUTION: 'session' variable might not be in context unless we pass it or usage of request.session
    # In Flask templates 'session' is global. In Django, we need `request.session`.
    # Replace `session.get('key')` with `request.session.key` (simplified)
    # Or `session['key']`.
    # Regex: session.get('xyz') -> request.session.xyz
    # Regex: session['xyz'] -> request.session.xyz
    
    content = re.sub(r"session\.get\(['\"](\w+)['\"]\)", r"request.session.\1", content)
    content = re.sub(r"session\['(\w+)'\]", r"request.session.\1", content)
    
    # 5. Fix flash messages
    # Flask: with messages = get_flashed_messages(with_categories=true)
    # Django: if messages ... for message in messages ... message.tags
    # This requires structural change in base.html mostly.
    
    if filepath.endswith("base.html"):
        # Replace Flask flash block with Django messages block
        flask_flash_pattern = re.compile(r'{% with messages = get_flashed_messages.*?{% endwith %}', re.DOTALL)
        django_messages_block = """
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}
        """
        content = flask_flash_pattern.sub(django_messages_block, content)

    # 6. Filters
    # nl2br -> linebreaksbr
    content = content.replace('|nl2br', '|linebreaksbr')

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

def main():
    if not os.path.exists(TEMPLATE_DIR):
        print(f"Directory not found: {TEMPLATE_DIR}")
        return

    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if file.endswith(".html"):
                convert_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
