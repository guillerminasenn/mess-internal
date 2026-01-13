clear;
setup = setup_synthetic();
max_dim = setup.max_dim;
runs = setup.runs;

for num_dims = 1:max_dim
    dim(num_dims) = load(sprintf('results/lss_synthetic_%dd', num_dims));
end

total_calls       = zeros(runs, max_dim);
effective_samples = zeros(runs, max_dim);
elapsed_time      = zeros(runs, max_dim);

for run=1:runs
  for num_dims=1:10
    total_calls(run, num_dims)       = sum(dim(num_dims).results(run).num_calls);
    effective_samples(run, num_dims) = dim(num_dims).results(run).effective_samples;
    elapsed_time(run, num_dims)      = dim(num_dims).results(run).elapsed;
  end
end

subplot(3,1,1);
boxplot(total_calls);
title('Number of likelihood evaluations');
xlabel('');

subplot(3,1,2);
boxplot(effective_samples);
title('Effective number of samples');
xlabel('');

subplot(3,1,3);
boxplot(elapsed_time);
title('Elapsed time');
xlabel('Number of dimensions');

