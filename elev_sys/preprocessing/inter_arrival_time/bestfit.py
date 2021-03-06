import warnings
import numpy as np
import pandas as pd
import scipy.stats as st

def time_difference(time):
    time = pd.to_datetime(time)
    return (time.values[1:]-time.values[:-1])/np.timedelta64(1,'s')

def best_fit_distribution(data, bins=15, ax=None):
    """Model data by finding best fit distribution to data"""
    # Get histogram of original data
    y, x = np.histogram(data, bins=bins, density=True)
    x = (x + np.roll(x, -1))[:-1] / 2.0

    # Distributions to check
    DISTRIBUTIONS = [        
        st.alpha,st.anglit,st.arcsine,st.beta,st.betaprime,st.bradford,st.burr,st.cauchy,st.chi,st.chi2,st.cosine,
        st.dgamma,st.dweibull,st.erlang,st.expon,st.exponnorm,st.exponweib,st.exponpow,st.f,st.fatiguelife,st.fisk,
        st.foldcauchy,st.foldnorm,st.frechet_r,st.frechet_l,st.genlogistic,st.genpareto,st.gennorm,
        st.genextreme,st.gausshyper,st.gamma,st.gengamma,st.genhalflogistic,st.gilbrat,st.gompertz,st.gumbel_r,
        st.gumbel_l,st.halfcauchy,st.halflogistic,st.halfnorm,st.halfgennorm,st.hypsecant,st.invgamma,st.invgauss,
        st.invweibull,st.johnsonsb,st.johnsonsu,st.ksone,st.kstwobign,st.laplace,st.levy,st.levy_l,
        st.logistic,st.loglaplace,st.lognorm,st.lomax,st.maxwell,st.mielke,st.nakagami,st.ncx2,
        st.pareto,st.pearson3,st.powerlognorm,st.powernorm,st.reciprocal,
        st.rayleigh,st.rice,st.t,st.triang,st.truncexpon,st.truncnorm,
        st.uniform,st.vonmises,st.wald
    ]

    # Best holders
    best_distribution = st.norm
    best_params = (0.0, 1.0)
    best_sse = np.inf

    # Estimate distribution parameters from data
    for distribution in DISTRIBUTIONS:

        # Try to fit the distribution
        try:
            # Ignore warnings from data that can't be fit
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore')

                # fit dist to data
                params = distribution.fit(data)

                # Separate parts of parameters
                arg = params[:-2]
                loc = params[-2]
                scale = params[-1]

                # Calculate fitted PDF and error with fit in distribution
                pdf = distribution.pdf(x, loc=loc, scale=scale, *arg)
                sse = np.sum(np.power(y - pdf, 2.0))

                # if axis pass in add to plot
                try:
                    if ax:
                        pd.Series(pdf, x).plot(ax=ax)
                    end
                except Exception:
                    pass

                # identify if this distribution is better
                if best_sse > sse > 0:
                    best_distribution = distribution
                    best_params = params
                    best_sse = sse

        except Exception:
            pass

    return (best_distribution.name, best_params)

def output_best_fit_df(data_path):
    Community_pd = pd.read_json(data_path)
    Community_pd['time'] = Community_pd['result'].apply(lambda x:x['timestamp'])
    Community_pd['from'] = Community_pd['result'].apply(lambda x:x['from'])
    df = pd.DataFrame(columns=['floor','best_fit_name','best_fit_params'])

    for i,row in Community_pd.groupby('from'):
        diff = time_difference(row['time'])
        best_fit_name, best_fit_params = best_fit_distribution(diff, 15)
        new_row = {'floor':i,'best_fit_name':best_fit_name,'best_fit_params':best_fit_params}
        df = df.append(new_row,ignore_index='True')
    
    df.to_csv(data_path[:-5]+'_BestFit.csv')


# path = '../data/北棟客梯_outer_diff_floor_01_down'
# time = pd.read_csv(path).iloc[:, 1:]['time']
# diff = time_difference(time)
# best_fit_name, best_fit_params = best_fit_distribution(diff, 15)

# output every df['best_fit_name','best_fit_params'] for a field
data_path = '../data/Field3_Hotel.json'
output_best_fit_df(data_path)