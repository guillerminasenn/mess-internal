function run_titsias_usps()
% Run the titsias on the usps data.

experiment_setup()

% Structure containing precomputed data for all usps experiments:
setup = setup_usps();
name  = 'titsias_usps';

fn = @(run) usps_run(setup, run);
success = experiment_run(name, setup.runs, fn, true);

function titsias_results = usps_run(setup, run)

addpath('titsias');
addpath('titsias/toolbox');

UNPACK_STRUCT(setup);

% MCMC options
mcmcoptions = mcmcOptions('controlPnts');
mcmcoptions.train.StoreEvery     = 1;
mcmcoptions.train.Burnin         = setup.burn;
mcmcoptions.train.T              = setup.iterations;
mcmcoptions.train.Store          = 0;
mcmcoptions.train.disp           = 0;
mcmcoptions.adapt.incrNumContrBy = 20;
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
fprintf('Run %03d/%3d Effective Samples: %0.2f  %0.2f secs  %d calls\n\n', ...
  run, runs, titsias_results.effective_samples, elapsed, titsias_results.num_calls);

