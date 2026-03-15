"""
Parameter sweep driver: builds the Rust simulator (release) and runs it over a small grid.
For each run it calls the Python analyzer and records summary metrics to `python/sweep_results.csv`.
"""
import subprocess
import itertools
import csv
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SIM = os.path.join(ROOT, 'rust_simulator')
BIN = os.path.join(SIM, 'target', 'release', 'rust_simulator')

def build():
    print('Building Rust simulator (release)...')
    subprocess.run(['cargo', 'build', '--release'], cwd=SIM, check=True)

def run_sim(alpha, beta, gamma, seed, steps=5000, out='data/sim.csv'):
    out_path = os.path.join(ROOT, out)
    cmd = [BIN, '--steps', str(steps), '--alpha', str(alpha), '--beta', str(beta), '--gamma', str(gamma), '--seed', str(seed), '--output', out_path]
    print('Running:', ' '.join(cmd))
    subprocess.run(cmd, cwd=SIM, check=True)
    return out_path

def analyze(path):
    cmd = [sys.executable, os.path.join(ROOT, 'python', 'analyze.py'), path]
    print('Analyzing:', path)
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.stdout

def main():
    build()
    alphas = [0.3, 0.5]
    betas = [20.0, 50.0]
    gammas = [0.5, 1.0]
    seeds = [1, 2]

    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    results_file = os.path.join(ROOT, 'python', 'sweep_results.csv')
    with open(results_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['alpha','beta','gamma','seed','analysis_stdout'])
        for a,b,g,s in itertools.product(alphas, betas, gammas, seeds):
            out = f'data/sim_a{a}_b{b}_g{g}_s{s}.csv'
            path = run_sim(a,b,g,s,steps=3000,out=out)
            stdout = analyze(os.path.relpath(path, ROOT))
            writer.writerow([a,b,g,s,stdout.replace('\n','\\n')])
    print('Sweep complete — results in', results_file)

if __name__ == '__main__':
    main()
