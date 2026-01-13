
num_steps  = 10;
step_sizes = logspace(-2, -0.5, num_steps);

iterations = 30000;
burn       = 1000;

load('data/synthetic.mat');

effective_samples = zeros([num_steps 10]);

for s = 1:num_steps
  step_size = step_sizes(s);
  for num_dims = 1:10

    counting_log_like_fn = add_call_counter(@(x) -0.5*numel(x)*log(2*pi*noise_variance) ...
      - (0.5/noise_variance)*sum((data{num_dims}.obs_f(:)-x(:)).^2));
    
    ff           = data{num_dims}.init_f;
    cur_log_like = counting_log_like_fn(ff);
    idx          = 0;
    samples      = zeros([num_data iterations]);
    loglikes     = zeros([1 iterations]);
    num_calls    = zeros([1 iterations + burn]);
    for ii = (1-burn):iterations
      if mod(ii,100) == 0
        fprintf('%0.3f] %02d-d Iter %05d / %05d\r', step_size, num_dims, ii, iterations);
      end
      
      [ff, cur_log_like] = gppu_underrelax(step_size, ff, data{num_dims}.chol_cov, counting_log_like_fn, cur_log_like);
      
      num_calls(ii + burn) = counting_log_like_fn();
      
      if ii > 0
        samples(:, ii) = ff;
        loglikes(ii)   = cur_log_like;
      end
    end

    effective_samples(s,num_dims) = effective_size_rcoda(loglikes(:));
  end
end

bar(step_sizes, effective_samples);