with open('web/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('Checking web/app.js lines...')
depth = 0
in_str = None
in_comment = False

for line_idx, line in enumerate(lines, 1):
    i = 0
    while i < len(line):
        if not in_str and not in_comment and line[i:i+2] == '//':
            break
        if not in_str and not in_comment and line[i:i+2] == '/*':
            in_comment = True
            i += 2
            continue
        if in_comment:
            if line[i:i+2] == '*/':
                in_comment = False
                i += 2
                continue
            i += 1
            continue
        ch = line[i]
        if not in_str and ch in ('"', "'", '`'):
            in_str = ch
            i += 1
            continue
        elif in_str and ch == in_str and (i == 0 or line[i-1] != '\\'):
            in_str = None
            i += 1
            continue
        if in_str:
            i += 1
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth < 0:
                print(f"Error: negative depth at line {line_idx}: {line.strip()}")
        i += 1

print(f"Total lines: {len(lines)}, Final brace depth: {depth}")
