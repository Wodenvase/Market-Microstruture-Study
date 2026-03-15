"""Generate external series, run the Rust simulator with that series, and analyze results."""
import subprocess
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def main():
    out = os.path.join(ROOT, 'data', 'external.csv')
    # generate external series
    print('Generating external series...')
    subprocess.run([sys.executable, os.path.join(ROOT, 'python', 'gen_external.py'), '--steps', '5000', '--out', out], check=True)

    # build simulator
    print('Building simulator...')
    subprocess.run(['cargo', 'build', '--release'], cwd=os.path.join(ROOT, 'rust_simulator'), check=True)

    bin = os.path.join(ROOT, 'rust_simulator', 'target', 'release', 'rust_simulator')
    sim_out = os.path.join(ROOT, 'data', 'sim_external.csv')
    cmd = [bin, '--steps', '5000', '--seed', '123', '--output', sim_out, '--external', out, '--external-mode', 'replace']
    print('Running simulator with external driver...')
    subprocess.run(cmd, check=True)

    print('Analyzing...')
    subprocess.run([sys.executable, os.path.join(ROOT, 'python', 'analyze.py'), sim_out], check=True)

if __name__ == '__main__':
    main()
