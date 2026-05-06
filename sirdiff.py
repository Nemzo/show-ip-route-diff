import re
import sys
import json
import difflib
import argparse
import os
import shutil
import itertools
import unicodedata

# Enable ANSI escape sequences (colorization) for Windows Command Prompt/PowerShell
if os.name == 'nt':
    os.system('')

# Color code definitions
COLOR_ADD = '\033[92m'  # Green: Added/Changed lines (NEW)
COLOR_DEL = '\033[91m'  # Red: Removed lines (OLD)
COLOR_INFO= '\033[96m'  # Cyan: Line information
RESET = '\033[0m'       # Reset formatting

def load_hosts(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Host definition file ({config_path}) not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {config_path}.")
        sys.exit(1)

def normalize_and_translate(line, hosts_map, mask_time=True, shorten_if=True, translate_host=True):
    if shorten_if:
        line = re.sub(r'GigabitEthernet', 'GE', line, flags=re.IGNORECASE)
        line = re.sub(r'FastEthernet', 'FE', line, flags=re.IGNORECASE)
        line = re.sub(r'is directly connected', 'Connected', line, flags=re.IGNORECASE)

    if mask_time:
        line = re.sub(r'\b\d{2}:\d{2}:\d{2}\b', '<TIME>', line)
        line = re.sub(r'\b\d+[wd]\d+[dh]\b', '<TIME>', line)
    
    if translate_host:
        for ip, hostname in hosts_map.items():
            ip_pattern = r'\b' + re.escape(ip) + r'\b'
            replacement = f"{ip}[{hostname}]"
            line = re.sub(ip_pattern, replacement, line)
        
    return line

def process_file(filepath, hosts_map, mask_time, shorten_if, translate_host):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    result = []
    for line in lines:
        clean_line = line.rstrip('\r\n') + '\n'
        result.append(normalize_and_translate(clean_line, hosts_map, mask_time, shorten_if, translate_host))
    return result

def get_display_width(text):
    width = 0
    for c in text:
        if unicodedata.east_asian_width(c) in ('F', 'W', 'A'):
            width += 2
        else:
            width += 1
    return width

def pad_text(text, width):
    text = text.rstrip('\n')
    current_width = get_display_width(text)
    
    if current_width > width:
        res = ""
        w = 0
        for c in text:
            cw = 2 if unicodedata.east_asian_width(c) in ('F', 'W', 'A') else 1
            if w + cw > width - 3:
                return res + "..."
            res += c
            w += cw
        return res
    else:
        return text + " " * (width - current_width)

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def match_grep(o, n, keyword):
    if not keyword: 
        return True
    kw = keyword.lower()
    return (kw in (o or "").lower()) or (kw in (n or "").lower())

def get_intra_line_diff(old_str, new_str):
    matcher = difflib.SequenceMatcher(None, old_str, new_str)
    out_old = ""
    out_new = ""
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            out_old += old_str[i1:i2]
            out_new += new_str[j1:j2]
        elif op == 'replace':
            out_old += COLOR_DEL + old_str[i1:i2] + RESET
            out_new += COLOR_ADD + new_str[j1:j2] + RESET
        elif op == 'delete':
            out_old += COLOR_DEL + old_str[i1:i2] + RESET
        elif op == 'insert':
            out_new += COLOR_ADD + new_str[j1:j2] + RESET
    return out_old, out_new

def process_unified_chunk(minus_lines, plus_lines, md_format, inline_diff):
    res = []
    if inline_diff and len(minus_lines) == len(plus_lines) and not md_format and len(minus_lines) > 0:
        for m, p in zip(minus_lines, plus_lines):
            m_text = m[1:] 
            p_text = p[1:] 
            o_col, n_col = get_intra_line_diff(m_text, p_text)
            res.append(COLOR_DEL + "-" + RESET + o_col)
            res.append(COLOR_ADD + "+" + RESET + n_col)
    else:
        for m in minus_lines:
            res.append(m if md_format else COLOR_DEL + m + RESET)
        for p in plus_lines:
            res.append(p if md_format else COLOR_ADD + p + RESET)
    return res

def display_side_by_side(old_lines, new_lines, file1, file2, diff_only=False, grep_keyword=None, md_format=False, inline_diff=False):
    output = []
    
    if md_format:
        output.append(f"| Status | OLD ({file1}) | NEW ({file2}) |\n")
        output.append("|:---:|---|---|\n")
    else:
        terminal_width = shutil.get_terminal_size().columns
        col_width = max((terminal_width - 5) // 2, 48) 
        output.append("[Legend]\n")
        output.append("  ! : Changed line (e.g., next-hop or interface changed)\n")
        output.append("  + : Added line (Only in NEW)\n")
        output.append("  - : Removed line (Only in OLD)\n")
        output.append("-" * (col_width * 2 + 5) + "\n")
        
        header_old = pad_text(f"--- OLD ({file1})", col_width)
        header_new = pad_text(f"+++ NEW ({file2})", col_width)
        
        output.append(f"  {header_old} | {header_new}\n")
        output.append("-" * (col_width * 2 + 5) + "\n")

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    has_diff = False
    
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            if not diff_only:
                for o, n in zip(old_lines[i1:i2], new_lines[j1:j2]):
                    if not match_grep(o, n, grep_keyword): continue
                    
                    if md_format:
                        o_clean, n_clean = o.strip().replace('|', '\\|'), n.strip().replace('|', '\\|')
                        output.append(f"| | {o_clean} | {n_clean} |\n")
                    else:
                        output.append(f"  {pad_text(o, col_width)} | {pad_text(n, col_width)}\n")
        elif op == 'replace':
            has_diff = True
            for o, n in itertools.zip_longest(old_lines[i1:i2], new_lines[j1:j2], fillvalue=""):
                if not match_grep(o, n, grep_keyword): continue
                
                if md_format:
                    o_clean, n_clean = o.strip().replace('|', '\\|'), n.strip().replace('|', '\\|')
                    output.append(f"| **Changed** | `{o_clean}` | `{n_clean}` |\n")
                else:
                    o_padded, n_padded = pad_text(o, col_width), pad_text(n, col_width)
                    if inline_diff:
                        o_col, n_col = get_intra_line_diff(o_padded, n_padded)
                        output.append(f"! {o_col} | {n_col}\n")
                    else:
                        output.append(f"! {COLOR_DEL}{o_padded}{RESET} | {COLOR_ADD}{n_padded}{RESET}\n")
        elif op == 'delete':
            has_diff = True
            for o in old_lines[i1:i2]:
                if not match_grep(o, "", grep_keyword): continue
                
                if md_format:
                    o_clean = o.strip().replace('|', '\\|')
                    output.append(f"| **Removed** | `{o_clean}` | |\n")
                else:
                    o_str = pad_text(o, col_width)
                    n_str = " " * col_width
                    output.append(f"- {COLOR_DEL}{o_str}{RESET} | {n_str}\n")
        elif op == 'insert':
            has_diff = True
            for n in new_lines[j1:j2]:
                if not match_grep("", n, grep_keyword): continue
                
                if md_format:
                    n_clean = n.strip().replace('|', '\\|')
                    output.append(f"| **Added** | | `{n_clean}` |\n")
                else:
                    o_str = " " * col_width
                    n_str = pad_text(n, col_width)
                    output.append(f"+ {o_str} | {COLOR_ADD}{n_str}{RESET}\n")
                
    if not has_diff:
        if md_format:
            output.append("\n**No route differences found (only uptime updates).**\n")
        else:
            output.append("\nNo route differences found (only uptime updates).\n")
        
    return output

def display_unified(old_lines, new_lines, file1, file2, diff_only=False, grep_keyword=None, md_format=False, inline_diff=False):
    output = []
    if md_format:
        output.append("```diff\n")
        
    context_lines = 0 if diff_only else 2
    diff = difflib.unified_diff(
        old_lines, new_lines, 
        fromfile=file1, tofile=file2, 
        n=context_lines 
    )

    has_diff = False
    minus_buffer = []
    plus_buffer = []

    def flush_buffers():
        nonlocal output
        if minus_buffer or plus_buffer:
            output.extend(process_unified_chunk(minus_buffer, plus_buffer, md_format, inline_diff))
            minus_buffer.clear()
            plus_buffer.clear()

    for line in diff:
        is_header = line.startswith('---') or line.startswith('+++') or line.startswith('@@')
        
        if grep_keyword and not is_header:
            if grep_keyword.lower() not in line.lower():
                continue

        has_diff = True
        
        if is_header:
            flush_buffers()
            if not diff_only:
                if md_format:
                    output.append(line)
                else:
                    if line.startswith('@@'):
                        output.append(COLOR_INFO + line + RESET)
                    else:
                        output.append(line)
        elif line.startswith('-') and not line.startswith('---'):
            minus_buffer.append(line)
        elif line.startswith('+') and not line.startswith('+++'):
            plus_buffer.append(line)
        else:
            flush_buffers()
            if not diff_only:
                output.append(line)
                
    flush_buffers()
            
    if not has_diff:
        output.append("No route differences found (only uptime updates).\n")
        
    if md_format:
        output.append("```\n")
        
    return output

def main():
    parser = argparse.ArgumentParser(
        prog="sirdiff",
        description="SirDiff (show-ip-route-diff) - A 'show ip route' diff tool for network engineers.\n"
                    "Ignores uptime fluctuations and extracts only true differences caused by configuration changes.",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("file1", help="Old route file (File 1)")
    parser.add_argument("file2", help="New route file (File 2)")
    
    group = parser.add_argument_group("Options")
    group.add_argument("-c", "--config", default="hosts.json", metavar="FILE", help="IP-to-hostname definition file (Default: hosts.json)")
    group.add_argument("-t", "--keep-time", action="store_true", help="Do not mask uptime, display as is")
    group.add_argument("-f", "--full-int", action="store_true", help="Do not abbreviate interface names (e.g., keep GigabitEthernet)")
    group.add_argument("-a", "--all-raw", action="store_true", help="Disable hostname translation, uptime masking, and IF abbreviation (raw diff)")
    group.add_argument("-u", "--unified", action="store_true", help="Display differences in a unified (vertical) format instead of side-by-side")
    group.add_argument("-d", "--diff-only", action="store_true", help="Hide unchanged lines and display only the differences")
    group.add_argument("-g", "--grep", metavar="KEYWORD", help="Extract only routes containing the specified string (IP, hostname, etc.)")
    group.add_argument("-i", "--inline", action="store_true", help="Colorize only the changed characters/words within modified lines")
    group.add_argument("--md", action="store_true", help="Output and save in Markdown format (for reports and tech blogs)")
    group.add_argument("-o", "--output", metavar="FILE", help="Save the diff result to the specified file")
    group.add_argument("-h", "--help", "-help", action="help", default=argparse.SUPPRESS, help="Show this help message and exit")
    
    args = parser.parse_args()

    hosts_map = load_hosts(args.config)
    
    if args.all_raw:
        mask_time = False
        shorten_if = False
        translate_host = False
    else:
        mask_time = not args.keep_time
        shorten_if = not args.full_int
        translate_host = True

    try:
        old_lines = process_file(args.file1, hosts_map, mask_time, shorten_if, translate_host)
        new_lines = process_file(args.file2, hosts_map, mask_time, shorten_if, translate_host)
    except Exception as e:
        print(f"File read error: {e}")
        sys.exit(1)

    if args.unified:
        result_lines = display_unified(old_lines, new_lines, args.file1, args.file2, args.diff_only, args.grep, args.md, args.inline)
    else:
        result_lines = display_side_by_side(old_lines, new_lines, args.file1, args.file2, args.diff_only, args.grep, args.md, args.inline)

    for line in result_lines:
        sys.stdout.write(line)

    if args.output:
        if os.path.exists(args.output):
            print(f"\n\033[93m[WARNING] File '{args.output}' already exists.\033[0m")
            ans = input("Do you want to overwrite? [y/N]: ").strip().lower()
            if ans not in ['y', 'yes']:
                print("[INFO] File save cancelled.")
                sys.exit(0)

        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                for line in result_lines:
                    f.write(strip_ansi(line))
            print(f"\n[INFO] Diff results saved to {args.output}")
        except Exception as e:
            print(f"\n[ERROR] Failed to save file: {e}")

if __name__ == "__main__":
    main()