function results = experiment_load(name, run);
%EXPERIMENT_LOAD load results stored by EXPERIMENT_RUN.
%
%     results = experiment_load(name[, run]);
%
% Loads results created with experiment_run. An error of some sort will result
% from trying to read runs that haven't completed yet, or from requesting the
% number of runs stored if no results have been gathered together yet.
%
% Inputs:
%         name string Same name used as in experiment run
%          run    1x1 If missing, return a structure array with all results
%                     If >=1 return structure with just results from that run
%                     If 0 return the number of runs stored
%
% Outputs:
%     results  structure (array)
%
% See also: EXPERIMENT_RUN

% Iain Murray, January 2009

final_mat = experiment_mat(name);

if ~exist('run', 'var')
    ws = load(final_mat);
    results = ws.results;
elseif run == 0
    ws = load(final_mat, 'num_runs');
    results = ws.num_runs;
else
    mat = experiment_mat(name, run);
    try
        ws = load(mat);
        results = ws.results;
    catch
        ws = load(final_mat);
        results = ws.results(run);
    end
end
