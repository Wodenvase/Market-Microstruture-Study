"""Generate an external price series P_ext from P_gas, tau, x using the piecewise rule.
Writes CSV with column `P_ext` and optional source columns.
"""
import numpy as np
import pandas as pd
import argparse
import os

def generate(P_gas, tau, x, Q_baseload, HR, EI):
    P_ext = np.where(x > Q_baseload, HR * P_gas + tau * EI, 0.0)
    return P_ext

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', type=int, default=5000)
    parser.add_argument('--Q', type=float, default=0.5)
    parser.add_argument('--HR', type=float, default=1.0)
    parser.add_argument('--EI', type=float, default=1.0)
    parser.add_argument('--out', type=str, default='data/external.csv')
    args = parser.parse_args()

    n = args.steps
    t = np.arange(n)
    # synthetic drivers (user can replace with real series)
    P_gas = 50 + 5 * np.sin(2 * np.pi * t / 200.0) + np.random.randn(n) * 0.5
    tau = 0.5 + 0.1 * np.sin(2 * np.pi * t / 50.0)
    x = 0.4 + 0.3 * np.sin(2 * np.pi * t / 120.0) + np.random.randn(n) * 0.05

    P_ext = generate(P_gas, tau, x, args.Q, args.HR, args.EI)

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    df = pd.DataFrame({'P_gas': P_gas, 'tau': tau, 'x': x, 'P_ext': P_ext})
    df.to_csv(args.out, index=False)
    print('Wrote', args.out)

if __name__ == '__main__':
    main()
