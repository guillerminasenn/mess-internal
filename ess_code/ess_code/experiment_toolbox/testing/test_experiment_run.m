function test_experiment_run()

experiment_name = 'toyexperiment';

for num_runs = [6 12];
    success = experiment_run(experiment_name, num_runs, @test_fn, true);
end

results = experiment_load(experiment_name);
testequal([results.aa], 1:12);
testequal([results.bb], 2:2:24);

num_runs = experiment_load(experiment_name, 0);
testequal(num_runs, 12);

second = experiment_load(experiment_name, 2);
testequal(second.aa, 2);
testequal(second.bb, 4);

function results = test_fn(ii)

aa = ii;
bb = aa*2;
pause(.2);

results = struct('aa', aa, 'bb', bb);
