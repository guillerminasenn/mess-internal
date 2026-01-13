function setup = setup_mine()
% This is shared across all of the mine experiments.

addpath('titsias');
addpath('titsias/toolbox');

setup.runs        = 100;
setup.iterations  = 100000;
setup.burn        = 10000;
setup.bin_width   = 50;
[setup.X setup.Y] = get_mine_data(setup.bin_width);
setup.X = setup.X(:);
setup.Y = setup.Y(:);

[n D] = size(setup.X); 

rate_guess    = sum(setup.Y)/n;
ell_guess     = (max(setup.X, [], 1) - min(setup.X, [], 1)) / 3;
sig_var_guess = 1;

% Setup GP
setup.options                       = gpsampOptions('offsetPoissonRegr'); 
setup.options.constraints.likHyper  = 'fixed';
setup.options.constraints.kernHyper = 'fixed';
setup.model                         = gpsampCreate(setup.Y, setup.X, setup.options);
setup.log_sigstd                    = 0.5*log(sig_var_guess);
setup.log_ell                       = log(ell_guess);
setup.model.GP.logtheta             = [2*setup.log_ell 2*setup.log_sigstd];

% Offset for likelihood
setup.model.Likelihood.logtheta = log(rate_guess);

setup.K = kernCompute(setup.model.GP, setup.X);
