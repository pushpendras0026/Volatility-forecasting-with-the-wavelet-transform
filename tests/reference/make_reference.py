"""Optional: regenerate stat_tests_reference.csv with independent Python implementations.

Not needed to run the project (the CSV is shipped). Requires numpy, pandas, scipy and
statsmodels (validated with statsmodels 0.15.0, scipy 1.18.1). Run from anywhere:
    python tests/reference/make_reference.py
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss, bds
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
import warnings
warnings.simplefilter('ignore')

root = Path(__file__).resolve().parents[2]
manifest = pd.read_csv(root / 'data/manifest.csv')
rows = []
def add(series, sample, name, value):
    rows.append({'series': series, 'sample': sample, 'quantity': name, 'value': float(value)})

for _, m in manifest.iterrows():
    p = pd.read_csv(root / 'data' / m['file'])
    p['Date'] = pd.to_datetime(p['Date'])
    logp = np.log(p['Price'].to_numpy())
    r = np.diff(logp); dates = p['Date'].to_numpy()[1:]
    samples = {'training': (r[dates <= np.datetime64('2009-12-31')], logp[1:][dates <= np.datetime64('2009-12-31')]),
               'full': (r, logp[1:])}
    for sample, (x, lp) in samples.items():
        ds = m['dataset']
        add(ds, sample, 'JB', stats.jarque_bera(x).statistic)
        add(ds, sample, 'skew_z', stats.skewtest(x).statistic)
        add(ds, sample, 'kurt_z', stats.kurtosistest(x).statistic)
        add(ds, sample, 'K2', stats.normaltest(x).statistic)
        add(ds, sample, 'AD', stats.anderson(x, dist='norm').statistic)
        if len(x) <= 5000:
            sw = stats.shapiro(x); add(ds, sample, 'SW', sw.statistic); add(ds, sample, 'SW_p', sw.pvalue)
        a = adfuller(x, regression='c', autolag='AIC')
        add(ds, sample, 'ADF_tau', a[0]); add(ds, sample, 'ADF_p', a[1]); add(ds, sample, 'ADF_lag', a[2])
        add(ds, sample, 'ADF_nobs', a[3]); add(ds, sample, 'ADF_crit_5', a[4]['5%'])
        k = kpss(x, regression='c', nlags='auto')
        add(ds, sample, 'KPSS', k[0]); add(ds, sample, 'KPSS_lag', k[2]); add(ds, sample, 'KPSS_p', k[1])
        lb = acorr_ljungbox(x, lags=[24])
        add(ds, sample, 'Q24', lb['lb_stat'].iloc[0])
        add(ds, sample, 'ARCH_LM12', het_arch(x - x.mean(), nlags=12)[0])
        # Nonstationary check series: log price.
        a = adfuller(lp, regression='c', autolag='AIC'); add(ds, sample, 'logprice_ADF_tau', a[0]); add(ds, sample, 'logprice_ADF_p', a[1])
        k = kpss(lp, regression='c', nlags='auto'); add(ds, sample, 'logprice_KPSS', k[0])
        if sample == 'training':
            b = bds(x, max_dim=6)
            for d, z in zip(range(2, 7), b[0]):
                add(ds, sample, f'BDS_m{d}', z)
pd.DataFrame(rows).to_csv(Path(__file__).with_name('stat_tests_reference.csv'), index=False, float_format='%.12g')
print('rows', len(rows))
