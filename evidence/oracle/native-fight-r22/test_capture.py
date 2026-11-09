"""Fail-closed freshness checks for all three observer prefixes."""
import unittest

import capture_observer as driver


class PrefixTests(unittest.TestCase):
    def test_prefix_shapes(self):
        p = driver.tag_prefixes('m002-example-tag')
        self.assertEqual(p['root'], b'M002|m002-example-tag|')
        self.assertEqual(p['side'], b'M002SIDE|m002-example-tag,')
        self.assertEqual(p['literal'], b'M002LITERAL|m002-example-tag|')

    def test_stale_any_prefix_refused(self):
        p = driver.tag_prefixes('fresh-tag')
        for key in ('root', 'side', 'literal'):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, 'already present'):
                    driver.reject_stale_prelaunch(p[key] + b'noise\n', p)

    def test_clean_prelaunch_accepted(self):
        p = driver.tag_prefixes('fresh-tag')
        driver.reject_stale_prelaunch(b'AccountSettings:noise\n', p)


if __name__ == '__main__':
    unittest.main()
