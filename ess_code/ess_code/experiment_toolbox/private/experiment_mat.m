function mat_file = experiment_mat(name, run_number)

if nargin == 1
    mat_file = sprintf('%s%s.mat', experiment_base(), name);
else
    mat_file = sprintf('%s%s_run%03d.mat', experiment_base(), name, run_number);
end

