"""Boot the shipped SRG jar in an isolated production Forge server and reload its data."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import queue
import socket
import threading
import time
from release_common import release_jar

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', required=True, help='Path to a Java 17 executable')
    parser.add_argument('--server', type=Path, default=ROOT / 'build/production-smoke', help='Isolated directory with Forge 1.20.1-47.4.20 installed')
    args = parser.parse_args()
    server = args.server.resolve()
    arg_file = server / 'libraries/net/minecraftforge/forge/1.20.1-47.4.20' / ('win_args.txt' if os.name == 'nt' else 'unix_args.txt')
    if not arg_file.exists():
        raise RuntimeError('Install the official Forge 1.20.1-47.4.20 server into this isolated directory first')
    mods = server / 'mods'
    mods.mkdir(exist_ok=True)
    jar = release_jar()
    shutil.copy2(jar, mods / jar.name)
    for record in json.loads((ROOT / 'dependencies.lock.json').read_text()):
        source = ROOT / 'libs' / record['file']
        if hashlib.sha512(source.read_bytes()).hexdigest() != record['sha512']:
            raise RuntimeError(f'Dependency checksum mismatch: {source}')
        shutil.copy2(source, mods / source.name)
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        port = port_socket.getsockname()[1]
    (server / 'eula.txt').write_text('eula=true\n')
    (server / 'server.properties').write_text(
        f'server-ip=127.0.0.1\nserver-port={port}\nonline-mode=false\nmax-players=1\n'
        'level-name=smoke-test-world\nlevel-type=minecraft:flat\nview-distance=2\nsimulation-distance=2\n'
        'generator-settings={"layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],"biome":"minecraft:plains","structures":{}}\n'
        'generate-structures=false\nspawn-protection=0\n', encoding='utf-8')
    log_path = ROOT / 'build/verification/production-server.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('w', encoding='utf-8') as log:
        process = subprocess.Popen([args.java, '-Xmx2G', '@' + str(arg_file), '--nogui'], cwd=server,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace')
        lines = queue.Queue()
        def read_output():
            for line in process.stdout:
                log.write(line)
                log.flush()
                lines.put(line)
            lines.put(None)
        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        ready = reloaded = stopping = False
        deadline = time.monotonic() + 180
        try:
            while time.monotonic() < deadline:
                try:
                    line = lines.get(timeout=1)
                except queue.Empty:
                    continue
                if line is None:
                    break
                if not ready and 'Done (' in line:
                    ready = True
                    commands = ['setblock 0 90 0 minecraft:stone', 'setblock 0 91 0 bossesrise_delight:hunters_feast',
                                'setblock 2 90 0 minecraft:stone', 'setblock 2 91 0 bossesrise_delight:kraken_hotpot',
                                'summon block_factorys_bosses:yeti 0 92 5 {NoAI:1b}',
                                'effect give @e[type=block_factorys_bosses:yeti] bossesrise_delight:corrosive_venom 2 0 true',
                                'loot spawn 0 92 0 loot block_factorys_bosses:entities/yeti', 'reload']
                    process.stdin.write('\n'.join(commands) + '\n')
                    process.stdin.flush()
                elif ready and 'Reloading!' in line:
                    reloaded = True
                elif reloaded and 'advancements' in line and 'Loaded' in line and not stopping:
                    process.stdin.write('stop\n')
                    process.stdin.flush()
                    stopping = True
            if not ready or not reloaded or not stopping:
                raise RuntimeError('Production server startup or resource reload did not complete')
            if process.wait(timeout=30) != 0:
                raise RuntimeError('Production Forge exited with an error')
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=20)
            reader.join(timeout=5)
    text = log_path.read_text(encoding='utf-8', errors='replace')
    if any(value in text for value in ['Loading errors encountered', 'Exception in server tick loop', 'NoSuchMethodError', 'NoSuchFieldError']):
        raise RuntimeError('Production Forge reported a runtime error; inspect the log')
    if text.count('Changed the block at') < 4 or 'Summoned new' not in text or 'Applied effect' not in text:
        raise RuntimeError('Production item/effect/boss registration checks did not complete')
    result = {'status': 'passed', 'minecraft': '1.20.1', 'forge': '47.4.20',
              'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest(),
              'mode': 'Dedicated server boot with the production jar, both feast blocks placed, real Yeti summoned, corrosive effect applied, loot table evaluated, data reloaded, clean shutdown'}
    (ROOT / 'docs/production-server-test.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Production SRG jar passed standalone dedicated server startup, content checks and data reload.')


if __name__ == '__main__':
    main()
