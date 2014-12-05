"""
=============================================
Whitening evoked data with a noise covariance
=============================================

Evoked data are loaded and then whitened using a given
noise covariance matrix. It's an excellent
quality check to see if baseline signals match the assumption
of Gaussian whiten noise from which we expect values around
and less than 2 standard deviations. Covariance estimation and diagnostic plots
are based on [1].

References
----------
[1] Engemann D. and Gramfort A. Automated model selection in covariance
    estimation and spatial whitening of MEG and EEG signals. (in press.)
    NeuroImage.

"""
# Authors: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Denis A. Engemann <denis.engemann@gmail.com>
#
# License: BSD (3-clause)

print(__doc__)

import mne
from mne import io
from mne.datasets import sample
from mne.cov import compute_covariance, whiten_evoked
import matplotlib.pyplot as plt

###############################################################################
# Set parameters

data_path = sample.data_path()
raw_fname = data_path + '/MEG/sample/sample_audvis_filt-0-40_raw.fif'
event_fname = data_path + '/MEG/sample/sample_audvis_filt-0-40_raw-eve.fif'

raw = io.Raw(raw_fname)

raw.info['bads'] += ['MEG 2443']  # bads + 1 more
events = mne.read_events(event_fname)
event_id, tmin, tmax = 1, -0.2, 0.5
picks = mne.pick_types(raw.info, meg='grad', exclude='bads')
reject = dict(grad=4000e-13)

epochs = mne.Epochs(raw, events, event_id, tmin, tmax, picks=picks,
                    baseline=(None, 0), reject=reject, preload=True, proj=False)

# we only take a few events to demonstrate the problem of regularization
epochs = epochs[:15]

################################################################################
# Compute covariance using automated regularization
methods = 'diagonal_fixed', 'shrunk',  # the best will be selected
noise_covs = compute_covariance(epochs, method=methods, tmin=None,
                                tmax=0, n_jobs=1, return_estimators=True)

# the "return_estimator" flag returns all covariance estimators sorted by
# log-likelihood. Moreover the noise cov objects now contain extra info.

print([c['loglik'] for c in noise_covs])

################################################################################
# Show whitening

# unwhitened evoked response

evoked = epochs.average()
evoked.plot()
picks = mne.pick_types(evoked.info, meg='grad', eeg=False, exclude='bads')

# plot the whitened evoked data for to see if baseline signals match the
# assumption of Gaussian whiten noise from which we expect values around
# and less than 2 standard deviations. For the Global field power we expect
# a value of 1.

evoked_white = whiten_evoked(evoked, noise_covs[0], picks)
evoked_white.plot(unit=False, hline=[-2, 2])

fig_gfp, ax_gfp = plt.subplots(1)

times = evoked.times * 1e3

for noise_cov, kind, color in zip(noise_covs, ('best', 'worst'),
                                  ('steelblue', 'orange')):

    evoked_white = whiten_evoked(evoked, noise_cov, picks)
    this_method = noise_cov['method']  # extra info in cov
    gfp = (evoked_white.data[picks] ** 2).sum(axis=0) / len(picks)

    ax_gfp.plot(times, gfp, color=color, label=this_method)
    ax_gfp.set_xlabel('times [ms]')
    ax_gfp.set_ylabel('Global field power')
    ax_gfp.set_xlim(times[0], times[-1])
    ax_gfp.set_ylim(0, 20)

ax_gfp.axhline(1, color='red', linestyle='--',
               label='expected basline (Gaussian)')
ax_gfp.legend(loc='upper right')
fig_gfp.show()
