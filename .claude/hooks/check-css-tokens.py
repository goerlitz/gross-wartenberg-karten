#!/usr/bin/env python3
"""
PreToolUse hook for Edit/Write on index.html.

Blocks any edit that introduces a raw hardcoded color literal (hex or
rgb()/rgba()) into a CSS component rule outside the theme token-definition
blocks. Colors belong in the token blocks (:root / [data-theme="..."]);
every other rule must consume them via var(--...).

See project memory theme-token-only.md for the convention this enforces,
and CLAUDE.md's "No hardcoded values" rule.
"""
import json
import os
import re
import sys


TOKEN_BLOCK_HEAD_PATTERNS = [
    # Single-line :root rule (currently just --serif, but matches whatever's there).
    r':root\s*\{[^}]*--serif:[^}]*\}',
    # The three multi-line theme token blocks (brace-matched below, no nested braces expected).
    r':root\s*,\s*\[data-theme="dark"\]\s*\{',
    r'\[data-theme="light"\]\s*\{',
    r'\[data-theme="warm-dark"\]\s*\{',
]

HEX_COLOR_RE = re.compile(
    r'(?:[:,(])\s*(#[0-9a-fA-F]{3,4}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{8}\b)'
)
RGB_LITERAL_RE = re.compile(r'\brgba?\(\s*(?!var\()')


def find_token_block_spans(style_block):
    spans = []

    m = re.search(TOKEN_BLOCK_HEAD_PATTERNS[0], style_block)
    if m:
        spans.append((m.start(), m.end()))

    for pat in TOKEN_BLOCK_HEAD_PATTERNS[1:]:
        m = re.search(pat, style_block)
        if not m:
            continue
        depth = 0
        end = None
        for j in range(m.end() - 1, len(style_block)):
            c = style_block[j]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end is not None:
            spans.append((m.start(), end))

    return spans


def blank_out(text, spans):
    chars = list(text)
    for s, e in spans:
        for k in range(s, e):
            if chars[k] != '\n':
                chars[k] = ' '
    return ''.join(chars)


def find_violations(checkable_text):
    violations = []
    lines = checkable_text.splitlines()

    for m in HEX_COLOR_RE.finditer(checkable_text):
        line_no = checkable_text.count('\n', 0, m.start()) + 1
        line_text = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ''
        violations.append((line_no, line_text))

    for m in RGB_LITERAL_RE.finditer(checkable_text):
        line_no = checkable_text.count('\n', 0, m.start()) + 1
        line_text = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ''
        violations.append((line_no, line_text))

    return violations


def simulate_new_content(tool_name, tool_input):
    file_path = tool_input.get('file_path', '')

    if tool_name == 'Write':
        return tool_input.get('content', '')

    if tool_name == 'Edit':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current = f.read()
        except OSError:
            return None
        old_string = tool_input.get('old_string', '')
        new_string = tool_input.get('new_string', '')
        if not old_string or old_string not in current:
            return None
        if tool_input.get('replace_all'):
            return current.replace(old_string, new_string)
        return current.replace(old_string, new_string, 1)

    return None


def allow():
    sys.exit(0)


def deny(reason):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
        "systemMessage": reason,
    }
    print(json.dumps(output))
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        allow()
        return

    tool_name = payload.get('tool_name', '')
    tool_input = payload.get('tool_input', {}) or {}
    file_path = tool_input.get('file_path', '')

    if os.path.basename(file_path) != 'index.html':
        allow()
        return

    new_content = simulate_new_content(tool_name, tool_input)
    if new_content is None:
        allow()
        return

    style_match = re.search(r'<style[^>]*>(.*?)</style>', new_content, re.DOTALL | re.IGNORECASE)
    if not style_match:
        allow()
        return

    style_block = style_match.group(1)
    style_start = style_match.start(1)

    token_spans = find_token_block_spans(style_block)
    checkable = blank_out(style_block, token_spans)
    violations = find_violations(checkable)

    if not violations:
        allow()
        return

    file_line_offset = new_content.count('\n', 0, style_start)
    seen = set()
    report_lines = []
    for line_no, line_text in violations:
        real_line = file_line_offset + line_no
        key = (real_line, line_text)
        if key in seen:
            continue
        seen.add(key)
        report_lines.append(f"  line ~{real_line}: {line_text}")

    reason = (
        "Hardcoded color value outside the theme token blocks in index.html:\n"
        + "\n".join(report_lines)
        + "\nAdd it to the :root token block(s) instead and reference it via var(--...) here. "
        "See memory theme-token-only.md."
    )
    deny(reason)


if __name__ == '__main__':
    main()
