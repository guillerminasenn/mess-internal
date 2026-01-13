function success = experiment_run(name, num_runs, fn, pass_run_number);
%EXPERIMENT_RUN save results from multiple function runs. Can be run concurrently.
%
%     success = experiment_run(name, num_runs, fn, [pass_run_number=false]);
%
% You provide a function that returns a structure and that you want to be run
% num_runs times. In the end you will get the results in a structure array
% stored in a .mat file. Running this m-file once will achieve that, the runs
% will be run one after the other. You can also run this m-file many times
% concurrently with the same arguments and will get the same results, but
% faster.
%
% The individual runs are initially stored in separate .mat files containing a
% single structure. When all runs have been completed, the results are gathered
% together in a single .mat file holding a structure array. Use experiment_load
% to access the data so that you don't need to know the details of how this
% works.
%
% If later you want more runs, just run this again with num_runs set to a bigger
% number. After all the extra runs have been done, they will be appended to
% the previously gathered results.
%
% WARNING: Random seeds are set using the run number using the 'classic'
% (deprecated) method for doing this in Matlab.
%
% Care is taken to ensure that concurrent Matlab processes don't end up running
% the same job, or getting confused into missing out a job. This relies on known
% atomic file operations on POSIX systems (even over NFS). NOTE these safeguards
% will not work on Windows: YOU CANNOT SAFELY RUN CONCURRENT INSTANCES OF THIS
% FUNCTION ON WINDOWS.
%
% DISCLAIMER: I HAVEN'T ACTUALLY TESTED THIS ON WINDOWS AT ALL, it may well fall
% flat on its face.
%
% Inputs:
%                 name string arbitrary tag for this experiment
%             num_runs  1x1   total number of runs that should be done. Some may be
%                             done by other concurrently running instances.
%                   fn  @fn   A function that returns a struct to be saved.
%                             A runtime field is added to this struct if it doesn't
%                             already exist.
%      pass_run_number  bool  If false (default), fn() takes no arguments.
%                             If true, fn() takes the run number in 1:num_runs
%                             as an argument.
%
% Outputs:
%             success   bool  did the final gathering work? Could be a failure
%                             because another instance locked the gathering
%                             operation first.
%
% See also: EXPERIMENT_LOAD

% Iain Murray, January 2009, October 2009

if ~exist('pass_run_number', 'var')
    pass_run_number = false;
end
opts = {};

experiment = experiment_setup(name, num_runs);
while experiment.needs_runs
    if pass_run_number
        opts = {experiment.run};
    end

    % Ensures experiments are different and reproducible
    % Can always override this in fn(), but this seems like a sensible default.
    rand('twister', experiment.run); % best available in 7.4 (not fastest though)
    randn('state', experiment.run);  % didn't have twister option in 7.4

    try
        tic
        % This is where the experiment is actually run:
        result = fn(opts{:});
        runtime = toc;
        if ~isfield(result, 'runtime')
            result.runtime = runtime;
        end
        experiment = experiment_record(experiment, result);
    catch
        experiment = experiment_cleanup(experiment);
        rethrow(lasterror);
    end
end
success = experiment_gather(experiment);




function experiment = experiment_setup(experiment_name, num_runs)

experiment.name = experiment_name;
experiment.num_runs = num_runs;

base = experiment_base();
if ~exist(base, 'dir')
    success = mkdir(base);
    % test existence rather than success, in case another process created the
    % directory just before us:
    assert(exist(base, 'dir') ~= 0);
end

% It may be that we gathered a "complete" experiment before with fewer num_runs,
% and now we are asking for more runs. So find out how many gathered runs (if
% any) have already been done and don't redo those.
final_mat = experiment_mat(experiment_name);
if exist(final_mat, 'file')
    ws = load(final_mat, 'num_runs');
    next_run = ws.num_runs + 1;
else
    next_run = 1;
end

% Find and lock the next experiment that needs doing and isn't locked
for ii = next_run:num_runs
    % We may find that next_run has changed, and I don't want to fiddle with ii within a loop
    if ii < next_run
        continue
    end
    if run_lock(experiment_name, ii)
        % Check the run still needs doing (it could be we got the lock just
        % because this experiment has just been gathered since we last looked at
        % final_mat)
        if exist(final_mat, 'file')
            ws = load(final_mat, 'num_runs');
            next_run = ws.num_runs + 1;
            if ii < next_run
                continue;
            end
        end

        % Set up the needed run and get out of here.
        experiment.needs_runs = true;
        experiment.run = ii;
        try
            % Not supported in Octave at time of writing
            experiment.cleaner_handle = myCleanup(@() run_unlock(experiment_name, ii));
        end
        return
    end
end

experiment.needs_runs = false;


function name = experiment_lock(varargin)
name = [experiment_mat(varargin{:}), '.lock'];


function success = run_lock(name, run)

mat_file = experiment_mat(name, run);
lock_file = experiment_lock(name, run);
if exist(mat_file) || exist(lock_file)
    success = false;
    return;
end
fail = my_lock(lock_file);
success = ~fail;


function success = run_unlock(name, run)

lock_file = experiment_lock(name, run);
fail = mydelete(lock_file);
success = ~fail;


function experiment = experiment_cleanup(experiment)

if isfield(experiment, 'cleaner_handle')
    experiment.cleaner_handle = 0;
else
    run_unlock(experiment.name, experiment.run);
end


function experiment = experiment_record(experiment, result_struct)

mat_file = experiment_mat(experiment.name, experiment.run);
if ~exist('octave_config_info', 'builtin')
    save(mat_file, '-struct', 'result_struct');
else
    % TODO identify an Octave version where -struct is supported and check for
    % >= that, rather than assuming all Octave versions don't have it.
    save_struct(mat_file, result_struct);
end
experiment = experiment_cleanup(experiment);
experiment = experiment_setup(experiment.name, experiment.num_runs);


function success = experiment_gather(experiment)

success = 0;
num_runs = experiment.num_runs;

for ii = 1:num_runs
    if exist(experiment_lock(experiment.name, ii), 'file')
        warning('Failed to gather results as exeriment(s) still running');
        return
    end
end

final_mat = experiment_mat(experiment.name);
final_lock = experiment_lock(experiment.name);
fail = my_lock(final_lock);
if fail
    warning('Failed to gather results as another instance seems to be doing it.');
    return;
end
if exist(final_mat, 'file');
    ws = load(final_mat);
    results = ws.results;
    first_gather = length(ws.results) + 1;
else
    first_gather = 1;
end

if first_gather <= num_runs
    for ii = first_gather:num_runs
        mat = experiment_mat(experiment.name, ii);
        if ~exist(mat, 'file')
            warning(['Failed to gather due to missing result file: ', mat]);
            mydelete(final_lock);
            return
        end
        ws = load(mat);
        results(ii) = ws;
    end
    tmp_name = [final_mat, '.tmp'];
    save('-v7', tmp_name, 'results', 'num_runs');
    if ispc
        movefile(tmp_name, final_mat);
    else
        % I haven't tested movefile's properties on Unix, so I'm sticking with this:
        [fail, dummy] = my_system(['mv "', tmp_name, '" "', final_mat, '"']);
    end

    % Feeling daring: delete files that have been gathered.
    % Hopefully an error would have occurred if they weren't saved properly.
    for ii = first_gather:num_runs
        mat = experiment_mat(experiment.name, ii);
        mydelete(mat);
    end
end

% Remove lock on final_mat
mydelete(final_lock);
success = 1;


function fail = mydelete(filename)
if ispc
    delete(filename);
    fail = false; % again, the Windows implementation is flaky and untested.
else
    % Moving is an atomic operation on POSIX systems,
    if exist('octave_config_info', 'builtin')
        % See my_system() for why there's the 2>/dev/null here and not for Matlab
        [fail, dummy] = system(['mv "', filename, '" "', filename, '.delme" 2>/dev/null && rm "', filename, '.delme" 2>/dev/null']);
    else
        [fail, dummy] = system(['mv "', filename, '" "', filename, '.delme" && rm "', filename, '.delme"']);
    end
end

function varargout = my_system(str)
% Octave splurges standard error from system() commands onto the screen rather
% than returning it as part of the output. As Octave calls '/bin/sh' to run
% system() commands we can throw away stderr by adding '2>/dev/null'. (Note I
% would like to keep the output with '2>&1', but that relies on /bin/sh being
% bash and breaks on BSD and Debian/Ubuntu systems.) We can't add the
% redirection command in Matlab, because it uses tcsh to execute commands, which
% would choke on the redirection syntax.
if exist('octave_config_info', 'builtin')
    cmd_end = ' 2>/dev/null';
else
    cmd_end = '';
end
varargout = cell(1, nargout);
[varargout{:}] = system([str, cmd_end]);

function fail = my_lock(lock_file)
if ispc
    % This isn't a working locking mechanism, I would need to identify an atomic
    % operation on Windows and have a Windows machine with Matlab and Octave to test it.
    % (I haven't any existing locking code on the file exchange.)
    fail = exist(lock_file, 'file');
    if ~fail
        fid = fopen(lock_file, 'w');
        fclose(fid);
    end
else
    [fail, dummy] = my_system(['ln -s /dev/null "', lock_file, '"']);
end
