"""Quy tắc công khai dùng chung; không chứa mật khẩu."""
import itertools
import string
import unicodedata

SPECIALS = '!@#._'
CHARSET = string.ascii_letters + string.digits + string.punctuation
LEET = {'a': '@', 'e': '3', 'o': '0'}


def name_roots(profile):
    def normalize(value):
        value = value.replace('đ', 'd').replace('Đ', 'D')
        return ''.join(c for c in unicodedata.normalize('NFD', value)
                       if not unicodedata.combining(c))
    words = normalize(profile['full_name']).split()
    roots = words + [''.join(words), ''.join(w[0] for w in words)]
    if len(words) >= 2:
        roots.append(''.join(words[-2:]))
    roots.append(normalize(profile['nickname']).replace(' ', ''))
    return sorted({r for r in roots if r and r.isascii() and r.isalnum()})


def word_variants(word):
    for base in dict.fromkeys((word, word.lower(), word[:1].upper() + word[1:].lower())):
        yield base
        positions = [i for i, c in enumerate(base) if c.lower() in LEET]
        for count in (1, 2):
            for chosen in itertools.combinations(positions, count):
                chars = list(base)
                for i in chosen:
                    chars[i] = LEET[chars[i].lower()]
                yield ''.join(chars)


def generate_dictionary_candidates(profile):
    year = str(profile['birth_year'])
    seen = set()
    for root in name_roots(profile):
        for word in word_variants(root):
            for special, suffix in itertools.product(SPECIALS, (year, year[-2:])):
                candidate = word + special + suffix
                if 8 <= len(candidate) <= 12 and candidate not in seen:
                    seen.add(candidate)
                    yield candidate
