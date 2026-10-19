"""Validate generated SVGs before they can replace the output branch files."""
from pathlib import Path
import sys
import json
import hashlib
import xml.etree.ElementTree as ET

root = Path(sys.argv[1])
names = ("pacman-contribution-graph.svg", "pacman-contribution-graph-dark.svg")
manifest = root / 'pacman-provenance.json'
if manifest.is_symlink() or not manifest.is_file():
    raise SystemExit('Missing real-data provenance')
provenance = json.loads(manifest.read_text(encoding='utf-8'))
days = provenance['days']
canonical = json.dumps(days, ensure_ascii=False, separators=(',', ':')).encode()
if (provenance.get('username') != 'lls144' or not 365 <= len(days) <= 367
        or provenance['calendarSha256'] != hashlib.sha256(canonical).hexdigest()
        or sum(d['count'] for d in days) != provenance['total']
        or provenance['total'] <= 0):
    raise SystemExit('Invalid or empty contribution provenance')
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
