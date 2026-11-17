"""No runtime dependencies; curses is provided by Python on macOS/Linux."""
import argparse
import curses
import json
import os
from pathlib import Path
import sys


def discover(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    nodes = []
    def visit(directory, parent=None):
        # Never follow symlinks or traverse hidden/build/version-control directories.
        children = sorted((p for p in directory.iterdir()
                           if p.is_dir() and not p.is_symlink()
                           and not p.name.startswith('.')
                           and p.name not in {'node_modules', '__pycache__', 'dist', 'build'}),
                          key=lambda p: p.name.casefold())
        doc = directory / 'SKILL.md'
        if doc.is_symlink():
            doc = directory / '__ignored_symlink__'
        descendants = []
        for child in children:
            descendants.extend(visit(child, directory))
        if doc.is_file() or descendants:
            return [{'path': directory, 'parent': parent,
                     'doc': doc if doc.is_file() else None}] + descendants
        return []
    nodes = visit(root)
    return nodes


def context(nodes, selected):
    path = selected['path']
    parts = []
    for node in nodes:
        if node['doc'] and (node['path'] == path or node['path'] in path.parents):
            parts.append(f"# Source: {node['doc']}\n\n" +
                         node['doc'].read_text(encoding='utf-8', errors='replace'))
    return '\n\n---\n\n'.join(parts)


def choose(nodes, root, selector):
    for node in nodes:
        if str(node['path'].relative_to(root)) == selector:
            return node
    raise ValueError(f"Unknown node: {selector}")


def tui(stdscr, nodes, root, output):
    curses.curs_set(0)
    stdscr.keypad(True)
    expanded = {root}
    index = scroll = 0
    query = ''
    notice = 'Local files only. No AI service is called.'
    def put(y, x, value, attr=0):
        h, w = stdscr.getmaxyx()
        if 0 <= y < h and x < w - 1:
            try:
                stdscr.addnstr(y, x, value.replace('\t', '    '), max(0, w-x-1), attr)
            except curses.error:
                pass
    while True:
        visible = [n for n in nodes if
                   (query.casefold() in str(n['path'].relative_to(root)).casefold()
                    if query else all(p in expanded for p in n['path'].parents
                                      if p == root or root in p.parents))]
        index = min(index, max(0, len(visible)-1))
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        if h < 10 or w < 60:
            put(0, 0, 'Resize terminal to at least 60 x 10; q to quit')
        else:
            split = max(24, w // 3)
            put(0, 0, 'SKILL TREE | ' + str(root), curses.A_BOLD)
            put(1, 0, '↑↓ select  →/Enter expand  ← collapse  / search  e export  q quit')
            put(2, 0, 'Search: ' + query if query else notice)
            rows = h - 5
            start = max(0, index - rows + 1)
            for row, n in enumerate(visible[start:start+rows], 3):
                depth = len(n['path'].relative_to(root).parts)
                branch = any(c['parent'] == n['path'] for c in nodes)
                marker = ('−' if n['path'] in expanded else '+') if branch else '·'
                label = '  '*depth + marker + ' ' + n['path'].name
                put(row, 0, label[:split-2], curses.A_REVERSE if n == visible[index] else 0)
            if visible:
                selected = visible[index]
                doc = selected['doc']
                lines = (doc.read_text(encoding='utf-8', errors='replace').splitlines()
                         if doc else ['No SKILL.md here; select a child node.'])
                maxscroll = max(0, len(lines)-rows)
                scroll = min(scroll, maxscroll)
                for row, line in enumerate(lines[scroll:scroll+rows], 3):
                    put(row, split, line)
                put(h-1, 0, str(selected['path'].relative_to(root)) +
                    ' | PgUp/PgDn preview | r reload | Esc clear search')
        key = stdscr.getch()
        if key in (ord('q'), 3):
            return
        if key == 27:
            query = ''; index = scroll = 0
        elif key == ord('/'):
            curses.echo()
            try:
                stdscr.move(2, 0); stdscr.clrtoeol()
                stdscr.addstr(2, 0, 'Search: ')
                query = stdscr.getstr(2, 8, max(1, w-10)).decode('utf-8', errors='replace')
            finally:
                curses.noecho()
            index = scroll = 0
        elif key == ord('r'):
            nodes[:] = discover(root); index = scroll = 0
        elif visible:
            selected = visible[index]
            if key in (curses.KEY_DOWN, ord('j')):
                index = min(index+1, len(visible)-1); scroll = 0
            elif key in (curses.KEY_UP, ord('k')):
                index = max(0, index-1); scroll = 0
            elif key in (curses.KEY_RIGHT, 10, 13):
                if selected['path'] in expanded and key in (10, 13):
                    expanded.discard(selected['path'])
                else:
                    expanded.add(selected['path'])
            elif key == curses.KEY_LEFT:
                if selected['path'] in expanded:
                    expanded.discard(selected['path'])
                else:
                    parent = selected['parent']
                    index = next((i for i,n in enumerate(visible) if n['path']==parent), index)
                scroll = 0
            elif key == curses.KEY_NPAGE:
                scroll += max(1, h-6)
            elif key == curses.KEY_PPAGE:
                scroll = max(0, scroll-max(1, h-6))
            elif key == ord('e'):
                if output:
                    try:
                        with Path(output).open('x', encoding='utf-8') as f:
                            f.write(context(nodes, selected))
                        notice = f'Exported context: {output}'
                    except OSError as exc:
                        notice = str(exc)
                else:
                    notice = 'Use --output PATH to enable context export (never overwrites).'


def main():
    parser = argparse.ArgumentParser(description='Browse local SKILL.md folders in a terminal.')
    parser.add_argument('root', nargs='?', default='.', help='Knowledge tree directory')
    parser.add_argument('--list', action='store_true', help='List node paths without a TTY')
    parser.add_argument('--json', action='store_true', help='List nodes as JSON')
    parser.add_argument('--context', metavar='NODE', help='Print node + ancestor skills, e.g. IC_A/PHY/RX')
    parser.add_argument('--output', help='New context export file (existing files are preserved)')
    args = parser.parse_args()
    try:
        root = Path(args.root).resolve()
        nodes = discover(root)
        if not nodes:
            raise ValueError('No SKILL.md found. Try the examples/connsys directory.')
        if args.json:
            print(json.dumps([{'path': str(n['path'].relative_to(root)),
                               'skill': str(n['doc']) if n['doc'] else None}
                              for n in nodes], ensure_ascii=False, indent=2))
        elif args.list:
            print('\n'.join(str(n['path'].relative_to(root)) for n in nodes))
        elif args.context is not None:
            content = context(nodes, choose(nodes, root, args.context))
            if args.output:
                with Path(args.output).open('x', encoding='utf-8') as f:
                    f.write(content)
            else:
                print(content)
        else:
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                raise ValueError('Interactive UI requires a terminal. Use --list, --json or --context NODE in an AI tool.')
            curses.wrapper(tui, nodes, root, args.output)
    except (ValueError, OSError, curses.error) as exc:
        parser.exit(1, f'skill-tree: {exc}\n')
    except KeyboardInterrupt:
        pass
