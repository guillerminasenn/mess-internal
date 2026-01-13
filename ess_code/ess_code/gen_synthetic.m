% Generate synthetic data sets in 1-d through 10-d on the unit hypercube.

clear;

% Parameters.
seed           = 0;
num_data       = 200;
length_scale   = 1;
noise_variance = 0.09;
jitter         = 1e-9;
cov_func       = @(x1, x2) ugauss_Knm(x1/(sqrt(2)*length_scale), ...
                                      x2/(sqrt(2)*length_scale));

% Fix random seed.
rand('state', seed);
randn('state', seed);

% Create a dataset for each dimensionality.
max_dim = 10;
for num_dims=1:max_dim

  % Generate the input points.
  data{num_dims}.inputs = rand([num_dims num_data]);
  
  % Generate the true function.
  K    = cov_func(data{num_dims}.inputs, data{num_dims}.inputs);
  K    = K + jitter*eye(size(K));
  M    = K + noise_variance*eye(size(K));
  U    = chol(K);  
  data{num_dims}.true_f = U'*randn([num_data 1]);
  
  % All methods should share the same initialisation.
  data{num_dims}.init_f = U'*randn([num_data 1]);
  
  % The observed function is noisy.
  data{num_dims}.obs_f = data{num_dims}.true_f ...
    + sqrt(noise_variance)*randn([num_data 1]);
  
  % Might as well store the cholesky decomposition.
  data{num_dims}.cov      = K;
  data{num_dims}.chol_cov = U;
  
end

clear num_dims
save('data/synthetic.mat');
