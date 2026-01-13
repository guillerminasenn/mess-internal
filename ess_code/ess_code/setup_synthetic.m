function setup = setup_synthetic()
% This is shared across all of the synthetic experiments.

setup = load('data/synthetic.mat');
setup.runs        = 100;
setup.iterations  = 100000;
setup.burn        = 10000;

