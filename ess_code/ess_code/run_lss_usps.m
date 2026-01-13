function run_lss_usps()
% Run the lss on the usps data.

experiment_setup()

% Structure containing precomputed data for all usps experiments:
setup = setup_usps();
name  = 'lss_usps';

fn = @(run) usps_run(setup, run);
success = experiment_run(name, setup.runs, fn, true);

function lss_results = usps_run(setup, run)

UNPACK_STRUCT(setup);

loglikHandle         = str2func(['logL' model.Likelihood.type]);
counting_log_like_fn = add_call_counter(@(x) sum(loglikHandle(model.Likelihood, y_train, x)));

num_data     = length(y_train);
idx          = 0;
samples      = zeros([num_data iterations]);
loglikes     = zeros([1 iterations]);
num_calls    = zeros([1 iterations + burn]);
tic;
chol_cov     = chol(K);
ff           = chol_cov'*randn([num_data 1]);
cur_log_like = counting_log_like_fn(ff);

for ii = (1-burn):iterations
  if mod(ii,100) == 0
    fprintf('Run %03d/%3d Iter %05d / %05d\r', run, runs, ii, iterations);
  end

  [ff, cur_log_like] = gppu_lineslice(ff, chol_cov, counting_log_like_fn, cur_log_like);

  num_calls(ii + burn) = counting_log_like_fn();

  if ii > 0
    samples(:, ii) = ff;
    loglikes(ii)   = cur_log_like;
  end
end
elapsed = toc;

lss_results.num_calls         = num_calls;
lss_results.loglikes          = loglikes;
lss_results.elapsed           = elapsed;
lss_results.effective_samples = effective_size_rcoda(loglikes(:));
fprintf('Run %03d/%3d Effective Samples: %0.2f  %0.2f secs\n\n', ...
  run, runs, lss_results.effective_samples, elapsed);

