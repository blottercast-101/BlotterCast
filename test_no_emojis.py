import os
import unittest
import unicodedata

class TestNoEmojisAcrossUI(unittest.TestCase):
    def test_no_raw_emojis_in_frontend(self):
        targets = ['frontend']
        exclude_chars = {
            '\u2713', '\u2714', '\u2715', '\u2716', '\u2717', '\u2718',  # Form/ballot checkmark ticks
            '©', '®', '™', '§', '¶', '•', '–', '—', '“', '”', '‘', '’',
            '«', '»', '°', '±', '×', '÷', '¢', '£', '¥', '€', '₱', '✦'
        }

        def is_raw_emoji(ch):
            if ch in exclude_chars:
                return False
            cp = ord(ch)
            if cp < 128:
                return False
            if cp == 0x2139: # Information source ℹ
                return True
            in_emoji_range = (
                (0x1F000 <= cp <= 0x1FAFF) or
                (0x200D == cp) or
                (0x2190 <= cp <= 0x21FF) or
                (0x2300 <= cp <= 0x23FF) or
                (0x25A0 <= cp <= 0x25FF) or
                (0x2600 <= cp <= 0x27BF) or
                (0x2B00 <= cp <= 0x2BFF) or
                (0xFE00 <= cp <= 0xFE0F)
            )
            if in_emoji_range:
                cat = unicodedata.category(ch)
                if cat in ('So', 'Sk', 'Cf') or (0x1F300 <= cp <= 0x1FAFF) or (0x2300 <= cp <= 0x23FF) or (0x25A0 <= cp <= 0x25FF) or (0x2600 <= cp <= 0x27BF) or (0x2B00 <= cp <= 0x2BFF):
                    if cp in (0x2190, 0x2191, 0x2192, 0x2193, 0x2194, 0x2195):
                        return False
                    return True
            return False

        violations = []
        for target in targets:
            for root, dirs, files in os.walk(target):
                for f in files:
                    if f.endswith(('.html', '.js')):
                        path = os.path.join(root, f)
                        with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                            for line_no, line in enumerate(fp, 1):
                                found_emojis = [c for c in line if is_raw_emoji(c)]
                                if found_emojis:
                                    violations.append((path, line_no, ''.join(set(found_emojis)), line.strip()))

        self.assertEqual(len(violations), 0, f"Found {len(violations)} raw emoji occurrences: {violations[:5]}")

if __name__ == '__main__':
    unittest.main()
