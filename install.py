#!/usr/bin/env python3
"""Install a local command without pip, network access or administrator rights."""
import argparse
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--prefix', type=Path, default=Path.home()/'.local')
args = parser.parse_args()
root = Path(__file__).resolve().parent
bin_dir = args.prefix.expanduser().resolve()/'bin'
bin_dir.mkdir(parents=True, exist_ok=True)
target = bin_dir/'skill-tree'
launcher = ('#!' + sys.executable + '\nimport sys\n'
            + 'sys.path.insert(0, ' + repr(str(root)) + ')\n'
            + 'from skill_tree.cli import main\nmain()\n')
try:
    with target.open('x', encoding='utf-8') as f:
        f.write(launcher)
except FileExistsError:
    parser.exit(1, f'{target} already exists; remove it explicitly before reinstalling.\n')
target.chmod(0o755)
print(f'Installed: {target}\nKeep the repository at: {root}\nAdd {bin_dir} to PATH if needed.')
