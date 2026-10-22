"""Synthetic unit fixtures only; never published as contribution records."""
import copy
from datetime import date, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('validator', Path(__file__).parents[1] / 'validate_pacman.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def days(n=368):
    return [dict(date=(date(2025, 10, 19) + timedelta(days=i)).isoformat(),
                 count=int(i == 0), level='FIRST_QUARTILE' if i == 0 else 'NONE') for i in range(n)]


def manifest():
    d = days()
    return dict(username='lls144', source='https://api.github.com/graphql', generator=validator.GENERATOR,
                days=d, total=1, nonzeroDays=1, **{'from': d[0]['date'], 'to': d[-1]['date']},
                calendarSha256=hashlib.sha256(json.dumps(d, separators=(',', ':')).encode()).hexdigest())


class CalendarTests(unittest.TestCase):
    def test_lengths(self):
        for n in (365, 366, 367, 368, 369, 371):
            with self.subTest(n=n):
                self.assertEqual(validator.validate_days(days(n)), 1)
        for n in (364, 372):
            with self.subTest(n=n), self.assertRaisesRegex(ValueError, 'day count'):
                validator.validate_days(days(n))

    def test_dates(self):
        for value, message in [('2025-02-30', 'invalid date'), ('2025-2-03', 'invalid date'),
                               ('0000-01-01', 'invalid date'), (None, 'invalid date')]:
            d = days(); d[0]['date'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, message):
                validator.validate_days(d)
        d = days(); d[1] = d[0].copy()
        with self.assertRaisesRegex(ValueError, 'duplicate date'): validator.validate_days(d)
        d = days(); del d[10]
        with self.assertRaisesRegex(ValueError, 'non-contiguous'): validator.validate_days(d)
        d = days(); d[2], d[3] = d[3], d[2]
        with self.assertRaisesRegex(ValueError, 'non-contiguous'): validator.validate_days(d)

    def test_counts(self):
        for count in (-1, 1.5, '1', True, None, 2**53):
            d = days(); d[0]['count'] = count
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, 'invalid contribution count'):
                validator.validate_days(d)
        d = days(); d[0]['count'] = 2**53 - 1; d[1].update(count=1, level='FIRST_QUARTILE')
        with self.assertRaisesRegex(ValueError, 'total exceeds'): validator.validate_days(d)

    def test_invalid_structures_and_levels(self):
        with self.assertRaisesRegex(ValueError, 'must be an array'): validator.validate_days(None)
        d = days(); d[0] = None
        with self.assertRaisesRegex(ValueError, 'invalid day object'): validator.validate_days(d)
        for level in ('INVALID', [], None):
            d = days(); d[0]['level'] = level
            with self.subTest(level=level), self.assertRaisesRegex(ValueError, 'invalid contribution level'):
                validator.validate_days(d)
        d = days(); d[0]['level'] = 'NONE'
        with self.assertRaisesRegex(ValueError, 'count/level mismatch'): validator.validate_days(d)
        d[0]['count'] = 0
        with self.assertRaisesRegex(ValueError, 'all-zero'): validator.validate_days(d)

    def test_provenance(self):
        valid = manifest()
        validator.validate_provenance(valid)
        for field, value, message in [
            ('username', 'other', 'identity or source'), ('source', 'https://example.com', 'identity or source'),
            ('generator', 'other', 'generator'), ('calendarSha256', '0'*64, 'SHA-256'),
            ('total', 2, 'total mismatch'), ('total', True, 'total mismatch'),
            ('nonzeroDays', 2, 'nonzero day count'), ('from', '2025-01-01', 'date range'),
            ('to', '2026-01-01', 'date range'),
        ]:
            altered = copy.deepcopy(valid); altered[field] = value
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, message):
                validator.validate_provenance(altered)


if __name__ == '__main__':
    unittest.main()
