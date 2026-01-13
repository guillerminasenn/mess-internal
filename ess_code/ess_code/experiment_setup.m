function experiment_setup()
% Matlab setup needed for all experiments

addpath(genpath('experiment_toolbox'));
try % Stop errors in older Matlabs
    maxNumCompThreads(1);
end
