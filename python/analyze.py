import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def hill_estimator(x, k=None):
    x = np.sort(np.abs(x))[::-1]
    n = len(x)
    if k is None:
        k = max(10, int(0.05 * n))
    k = min(k, n-1)
    xk = x[:k]
    xm = xk[0]
    hill = (1.0 / k) * np.sum(np.log(xk / xm))
    alpha = 1.0 / hill if hill > 0 else np.nan
    return alpha

def hurst_exponent(ts):
    N = len(ts)
    T = np.arange(1, N+1)
    Y = np.cumsum(ts - np.mean(ts))
    R = np.maximum.accumulate(Y) - np.minimum.accumulate(Y)
    S = pd.Series(ts).rolling(window=20, min_periods=1).std().to_numpy()
    R_over_S = np.nanmean(R[1:] / (S[1:] + 1e-8))
    return np.log(R_over_S) / np.log(N) if R_over_S > 0 else np.nan

def main(path):
    df = pd.read_csv(path)
    price = df['price'].values
    returns = np.diff(np.log(price))

    print(f"N={len(returns)} returns")

    alpha = hill_estimator(np.abs(returns))
    print(f"Hill tail alpha estimate: {alpha:.3f}")

    hurst = hurst_exponent(returns)
    print(f"Approx Hurst exponent (rough): {hurst:.3f}")

    # plots
    sns.set(style='whitegrid')
    plt.figure(figsize=(10,6))
    plt.subplot(2,1,1)
    plt.plot(df['t'], df['price'])
    plt.title('Price')

    plt.subplot(2,1,2)
    plt.plot(df['t'][1:], returns)
    plt.title('Returns')
    plt.tight_layout()
    plt.savefig('python/price_returns.png')

    # volatility clustering: rolling std
    roll = pd.Series(returns).rolling(window=100).std()
    plt.figure()
    plt.plot(df['t'][1:], roll)
    plt.title('Rolling volatility (window=100)')
    plt.savefig('python/rolling_vol.png')

    print('Plots saved to python/price_returns.png and python/rolling_vol.png')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python analyze.py data/sim.csv')
    else:
        main(sys.argv[1])
