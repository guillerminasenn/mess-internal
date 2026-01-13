function test_locking_experiment()

% The code should lock the creation of experiments so that duplicates aren't
% run, even if this m-file is being run many times across machines using NFS to
% save results.

% This allows me to start the runs at a similar time by touching a marker file "GO"
while ~exist('GO','file')
    pause(0.01);
end

experiment_name = 'lockingexperiment';

for num_runs = [6 12];
    success = experiment_run(experiment_name, num_runs, @test_fn, true);
    pause(0.01);
end

function results = test_fn(ii)

aa = ii;
bb = aa*2;
pause(.5);

results = struct('aa', aa, 'bb', bb);
