import hashlib, hmac, subprocess, sys, tempfile, unittest
from pathlib import Path
from dnaid.core import canonical, identifier, read_panel
from dnaid.quality import read_vcf, validated_dosages

BASE = Path(__file__).resolve().parents[1]
EX = BASE / 'examples'

class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.panel = (EX / 'panel.tsv').read_bytes()
        self.policy = (EX / 'policy.json').read_bytes()
        self.rows = read_panel(self.panel)
        self.calls = [read_vcf(EX / (x + '.vcf')) for x in ('full', 'unconstrained', 'half-a', 'half-b')]

    def test_diploid_and_phasing(self):
        self.assertEqual(validated_dosages(self.rows, *self.calls), '012')

    def test_independent_hmac_reference(self):
        payload = canonical(self.panel, self.policy, '0' * 64, '012')
        key = bytes(range(32))  # synthetic TEST key, never for actual data
        expected = 'DNAID-H1-' + hmac.new(key, b'DNAID-HMAC-1\ncontext=test-v1\n' + payload, hashlib.sha256).hexdigest()
        self.assertEqual(identifier(payload, key, 'test-v1'), expected)
        self.assertTrue(payload.endswith(b'\n'))
        self.assertNotIn(b'\r', payload)

    def test_identity_changes(self):
        payload = canonical(self.panel, self.policy, '0' * 64, '012')
        token = identifier(payload, bytes(range(32)), 'test-v1')
        alternatives = [identifier(payload, b'x' * 32, 'test-v1'),
                        identifier(payload, bytes(range(32)), 'another-context'),
                        identifier(canonical(self.panel, self.policy, '0' * 64, '002'), bytes(range(32)), 'test-v1'),
                        identifier(canonical(self.panel, self.policy+b' ', '0' * 64, '012'), bytes(range(32)), 'test-v1')]
        self.assertTrue(all(x != token for x in alternatives))

    def test_missing_locus_rejected(self):
        del self.calls[0][('chr1', 100)]
        with self.assertRaises(ValueError):
            validated_dosages(self.rows, *self.calls)

    def test_depth_failure_rejected(self):
        self.calls[0][('chr1', 100)]['format']['DP'] = '1'
        with self.assertRaises(ValueError):
            validated_dosages(self.rows, *self.calls)

    def test_discordant_half_rejected(self):
        self.calls[2][('chr1', 200)]['format'].update(GT='0/0', AD='50,0', PL='0,100,200')
        with self.assertRaises(ValueError):
            validated_dosages(self.rows, *self.calls)

    def test_unconstrained_disagreement_rejected(self):
        self.calls[1][('chr1', 100)]['format']['GT'] = '0/1'
        with self.assertRaises(ValueError):
            validated_dosages(self.rows, *self.calls)

    def test_strand_failure_rejected(self):
        self.calls[0][('chr1', 200)]['format']['ADF'] = '25,0'
        with self.assertRaises(ValueError):
            validated_dosages(self.rows, *self.calls)

    def test_panel_and_missing_encoding_rejected(self):
        for panel in (self.panel.replace(b'chr2', b'chrX'), self.panel.replace(b'\n', b'\r\n'), self.panel + b'chr2\t100\tG\tA\n'):
            with self.assertRaises(ValueError): read_panel(panel)
        for digits in ('01', '01.', '013'):
            with self.assertRaises(ValueError): canonical(self.panel, self.policy, '0'*64, digits)
        with self.assertRaises(ValueError): identifier(b'x', b'x'*32, 'a\nb')

    def test_cli_and_key_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as d:
            key = Path(d) / 'secret.key'
            cmd = [sys.executable, '-m', 'dnaid', 'keygen', str(key)]
            self.assertEqual(subprocess.run(cmd, cwd=BASE, capture_output=True).returncode, 0)
            original = key.read_bytes()
            self.assertNotEqual(subprocess.run(cmd, cwd=BASE, capture_output=True).returncode, 0)
            self.assertEqual(key.read_bytes(), original)
            command = [sys.executable, '-m', 'dnaid', 'encode', '--panel', str(EX/'panel.tsv'), '--policy', str(EX/'policy.json'), '--key', str(key), '--reference-sha256', '0'*64, '--context', 'synthetic-demo-v1']
            for name in ('full', 'unconstrained', 'half-a', 'half-b'):
                command.extend(['--'+name, str(EX/(name+'.vcf'))])
            result = subprocess.run(command, cwd=BASE, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('DNAID-H1-', result.stdout)
            self.assertNotIn('genotypes', result.stdout)

if __name__ == '__main__': unittest.main()
