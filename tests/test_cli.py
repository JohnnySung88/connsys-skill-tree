import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from skill_tree.cli import discover, context, choose

class TreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        for name, body in [('SKILL.md', 'ROOT'), ('PHY/RX/SKILL.md', '接收'),
                           ('MAC/SKILL.md', 'MAC'), ('.secret/SKILL.md', 'SECRET')]:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding='utf-8')
        (self.root/'loop').symlink_to(self.root, target_is_directory=True)

    def test_hierarchy_and_context_isolation(self):
        nodes = discover(self.root)
        self.assertEqual([str(n['path'].relative_to(self.root)) for n in nodes],
                         ['.', 'MAC', 'PHY', 'PHY/RX'])
        result = context(nodes, choose(nodes, self.root, 'PHY/RX'))
        self.assertIn('ROOT', result)
        self.assertIn('接收', result)
        self.assertNotIn('\nMAC', result)
        self.assertNotIn('SECRET', result)

    def test_json_and_non_tty_error(self):
        args = [sys.executable, '-m', 'skill_tree', str(self.root)]
        proc = subprocess.run(args+['--json'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(len(json.loads(proc.stdout)), 4)
        proc = subprocess.run(args, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('requires a terminal', proc.stderr)

    def test_export_never_overwrites(self):
        target = self.root/'context.md'
        target.write_text('preserve')
        proc = subprocess.run([sys.executable, '-m', 'skill_tree', str(self.root),
                               '--context', 'PHY/RX', '--output', str(target)],
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(target.read_text(), 'preserve')

    def test_missing_root_and_unknown_node(self):
        with self.assertRaises(ValueError):
            discover(self.root/'missing')
        with self.assertRaises(ValueError):
            choose(discover(self.root), self.root, 'missing')

if __name__ == '__main__':
    unittest.main()
