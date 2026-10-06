"""Download pinned official Forge dependencies and verify SHA-512 hashes."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    (ROOT / 'libs').mkdir(exist_ok=True)
    records = json.loads((ROOT / 'dependencies.lock.json').read_text(encoding='utf-8'))
    for record in records:
        destination = ROOT / 'libs' / record['file']
        if not destination.exists():
            request = urllib.request.Request(record['url'], headers={'User-Agent': 'BossesRiseDelight-development/1.0.0'})
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
            if hashlib.sha512(data).hexdigest() != record['sha512']:
                raise RuntimeError(f"Download checksum mismatch: {record['file']}")
            destination.write_bytes(data)
        if hashlib.sha512(destination.read_bytes()).hexdigest() != record['sha512']:
            raise RuntimeError(f"Dependency checksum mismatch: {destination}")
        print(f"Verified {record['file']}")


if __name__ == '__main__':
    main()
