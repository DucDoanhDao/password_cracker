"""Kiểm tra các hành vi có ý nghĩa của thí nghiệm."""
import unittest
from unittest.mock import patch
import attack
import defense
from rules import CHARSET, generate_dictionary_candidates


class LabTests(unittest.TestCase):
    def test_collision_is_not_a_password_match(self):
        self.assertEqual(attack.modulo_hash('ab'), attack.modulo_hash('ba'))
        result = attack.crack_password(iter(['ba', 'ab']), attack.modulo_hash('ab'),
                                       attack.sha256_hash('ab'), 10, 5)
        self.assertEqual(result['recovered_password'], 'ab')
        self.assertEqual(result['false_positives'], 1)
        self.assertEqual(result['attempts'], 2)

    def test_stop_reasons(self):
        args = (attack.modulo_hash('zz'), attack.sha256_hash('zz'))
        exhausted = attack.crack_password(iter(['aa']), *args, 10, 5)
        limited = attack.crack_password(iter(['aa', 'bb']), *args, 1, 5)
        self.assertEqual(exhausted['stop_reason'], 'candidate_space_exhausted')
        self.assertEqual(limited['stop_reason'], 'max_attempts_reached')
        with patch.object(attack.time, 'perf_counter', side_effect=[0, 6, 6]):
            timed = attack.crack_password(iter(['aa']), *args, 10, 5)
        self.assertEqual(timed['stop_reason'], 'timeout_reached')
        self.assertEqual(timed['attempts'], 0)

    def test_bruteforce_enumerates_without_duplicates(self):
        self.assertEqual(list(attack.generate_bruteforce_candidates('ab', 2, 10)),
                         ['aa', 'ab', 'ba', 'bb'])

    def test_vietnamese_profile_and_two_leet_substitutions(self):
        profile = {'full_name': 'Nguyễn Văn An', 'nickname': 'Bao', 'birth_year': 1998}
        candidates = list(generate_dictionary_candidates(profile))
        self.assertIn('B@0!1998', candidates)
        self.assertIn('Nguyen!98', candidates)
        self.assertEqual(len(candidates), len(set(candidates)))
        self.assertTrue(all(8 <= len(c) <= 12 for c in candidates))

    def test_secure_password_and_hash_agreement(self):
        password = defense.generate_secure_password()
        self.assertEqual(len(password), 16)
        self.assertTrue(set(password) <= set(CHARSET))
        self.assertEqual(defense.sha256_hash(password), attack.sha256_hash(password))
        self.assertEqual(defense.modulo_hash(password), attack.modulo_hash(password))
        with self.assertRaises(ValueError):
            defense.generate_secure_password(8)


if __name__ == '__main__':
    unittest.main()
