function run_titsias_synthetic()
% Run the titsias on the synthetic data.

experiment_setup()

% Structure containing precomputed data for all synthetic experiments:
setup = setup_synthetic();

for num_dims = 1:setup.max_dim
    name = sprintf('titsias_synthetic_%dd', num_dims);
    fn = @(run) synthetic_run(setup, num_dims, run);
    success = experiment_run(name, setup.runs, fn, true);
end

function titsias_results = synthetic_run(setup, num_dims, run)

addpath('titsias');
addpath('titsias/toolbox');

UNPACK_STRUCT(setup);

counting_log_like_fn = add_call_counter(@(x) -0.5*numel(x)*log(2*pi*noise_variance) ...
  - (0.5/noise_variance)*sum((data{num_dims}.obs_f(:)-x(:)).^2));

ff           = data{num_dims}.init_f;
cur_log_like = counting_log_like_fn(ff);
idx          = 0;
samples      = zeros([num_data iterations]);
loglikes     = zeros([1 iterations]);
num_calls    = zeros([1 iterations + burn]);
tic;

% Setup GP
options                       = gpsampOptions('regression'); 
options.constraints.likHyper  = 'fixed';
options.constraints.kernHyper = 'fixed';
model                         = gpsampCreate(data{num_dims}.obs_f, data{num_dims}.inputs', options);
log_ell                       = repmat(log(length_scale), 1, num_dims);
log_sig_var                   = 0;
model.GP.logtheta             = [log_ell log_sig_var];
log_noise_var                 = log(noise_variance);
model.Likelihood.logtheta     = log_noise_var;

% MCMC options
mcmcoptions = mcmcOptions('controlPnts');
mcmcoptions.train.StoreEvery     = 1;
mcmcoptions.train.Burnin         = setup.burn;
mcmcoptions.train.T              = setup.iterations;
mcmcoptions.train.Store          = 0;
mcmcoptions.train.disp           = 0;
mcmcoptions.adapt.incrNumContrBy = 1;
mcmcoptions.adapt.disp           = 0;

% Do the adaptation.
tic;
[model PropDist samples accRates] = gpsampControlAdapt(model, mcmcoptions.adapt);

% Compensate for the different definition of "iterations"
num_control              = size(model.Fu, 2);
mcmcoptions.train.T      = ceil(setup.iterations/num_control);
mcmcoptions.train.Burnin = ceil(setup.burn/num_control);

% Acquire the samples.
[model PropDist samples accRates] = gpsampControlTrain(model, PropDist, mcmcoptions.train);
elapsed = toc;

titsias_results.num_calls         = setup.iterations + setup.burn;
titsias_results.loglikes          = samples.LogL(:);
titsias_results.elapsed           = elapsed;
titsias_results.effective_samples = effective_size_rcoda(titsias_results.loglikes(:));
fprintf('Run %03d/%3d %02d-d Effective Samples: %0.2f  %0.2f secs  %d calls\n\n', ...
  run, runs, num_dims, titsias_results.effective_samples, elapsed, titsias_results.num_calls);

