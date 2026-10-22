"""Validate generated SVGs before they can replace the output branch files."""
from pathlib import Path
import sys
import json
import hashlib
import xml.etree.ElementTree as ET

from datetime import date
import re

MAX_SAFE_INTEGER = 2**53 - 1
LEVELS = {'NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE'}
GENERATOR = 'abozanona/pacman-contribution-graph@7332e1de7903ab780c3692a4127a59cc13872daa'


def validate_days(days):
    # Same 53-column / full-week policy as the generation guard. Never pad/trim.
    if not isinstance(days, list):
        raise ValueError('calendar days must be an array')
    if not 365 <= len(days) <= 53 * 7:
        raise ValueError(f'calendar day count {len(days)} outside 365..371 (53 weeks)')
    seen, previous, total = set(), None, 0
    for index, day in enumerate(days):
        if not isinstance(day, dict):
            raise ValueError(f'invalid day object at index {index}')
        raw = day.get('date')
        if not isinstance(raw, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw):
            raise ValueError(f'invalid date at index {index}')
        try:
            current = date.fromisoformat(raw)
        except ValueError:
            raise ValueError(f'invalid date at index {index}') from None
        if raw in seen:
            raise ValueError(f'duplicate date at index {index}')
        if previous is not None and (current - previous).days != 1:
            raise ValueError(f'non-contiguous or unordered dates at index {index}')
        count, level = day.get('count'), day.get('level')
        if type(count) is not int or not 0 <= count <= MAX_SAFE_INTEGER:
            raise ValueError(f'invalid contribution count at index {index}')
        if not isinstance(level, str) or level not in LEVELS:
            raise ValueError(f'invalid contribution level at index {index}')
        if (count == 0) != (level == 'NONE'):
            raise ValueError(f'count/level mismatch at index {index}')
        seen.add(raw)
        previous = current
        total += count
    if total > MAX_SAFE_INTEGER:
        raise ValueError('contribution total exceeds safe integer range')
    if not total:
        raise ValueError('valid but all-zero calendar; no synthetic path')
    return total


def validate_provenance(provenance):
    if not isinstance(provenance, dict):
        raise ValueError('provenance must be an object')
    if provenance.get('username') != 'lls144' or provenance.get('source') != 'https://api.github.com/graphql':
        raise ValueError('unexpected contribution identity or source')
    if provenance.get('generator') != GENERATOR:
        raise ValueError('unexpected contribution generator')
    days = provenance.get('days')
    total = validate_days(days)
    # Rebuild canonical key order to match JSON.stringify in the Node guard.
    canonical = json.dumps([dict(date=d['date'], count=d['count'], level=d['level']) for d in days],
                           ensure_ascii=False, separators=(',', ':')).encode()
    if provenance.get('calendarSha256') != hashlib.sha256(canonical).hexdigest():
        raise ValueError('calendar SHA-256 mismatch')
    if type(provenance.get('total')) is not int or provenance['total'] != total:
        raise ValueError('contribution total mismatch')
    if type(provenance.get('nonzeroDays')) is not int or provenance['nonzeroDays'] != sum(d['count'] > 0 for d in days):
        raise ValueError('nonzero day count mismatch')
    if provenance.get('from') != days[0]['date'] or provenance.get('to') != days[-1]['date']:
        raise ValueError('calendar date range mismatch')


def main(root):
    names = ('pacman-contribution-graph.svg', 'pacman-contribution-graph-dark.svg')
    manifest = root / 'pacman-provenance.json'
    if manifest.is_symlink() or not manifest.is_file():
        raise SystemExit('Missing real-data provenance')
    provenance = json.loads(manifest.read_text(encoding='utf-8'))
    try:
        validate_provenance(provenance)
    except ValueError as error:
        raise SystemExit(f'Invalid contribution provenance: {error}') from None
    hashes = {}
    for name in names:
        file = root / name
        if file.is_symlink() or not file.is_file() or not 1024 <= file.stat().st_size <= 10_000_000:
            raise SystemExit(f"Invalid SVG file: {name}")
        doc = ET.parse(file)
        if doc.getroot().tag != "{http://www.w3.org/2000/svg}svg":
            raise SystemExit(f"Not an SVG: {name}")
        animated = False
        for element in doc.iter():
            tag = element.tag.rsplit("}", 1)[-1]
            if tag in {"script", "foreignObject"}:
                raise SystemExit(f"Executable content in {name}")
            animated |= tag in {"animate", "animateTransform"}
            for key, value in element.attrib.items():
                key = key.rsplit("}", 1)[-1]
                if key.lower().startswith("on"):
                    raise SystemExit(f"Event handler in {name}")
                if key in {"href", "src"} and not value.startswith(("#", "data:image/png;base64,", "data:image/jpeg;base64,")):
                    raise SystemExit(f"External image dependency in {name}")
        if not animated:
            raise SystemExit(f"Missing SVG animation: {name}")
        ns = {'s': 'http://www.w3.org/2000/svg'}
        frames = int(doc.findtext('.//s:metadata/s:info/s:frames', default='0', namespaces=ns))
        pacman = doc.find('.//*[@id="pacman"]')
        moves = [] if pacman is None else [e for e in pacman if e.get('type') == 'translate']
        eaten = [e for e in doc.iter() if e.get('id', '').startswith('c-') and len(e)]
        if frames <= 0 or not any(len(set(e.get('values', '').split(';'))) > 1 for e in moves) or not eaten:
            raise SystemExit(f'No actual movement/eating animation: {name}')
        hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest()
        print(f"OK {name}: {file.stat().st_size} bytes")
    if 'svgSha256' in provenance and provenance['svgSha256'] != hashes:
        raise SystemExit('SVG hashes do not match generation provenance')
    provenance['svgSha256'] = hashes
    manifest.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
