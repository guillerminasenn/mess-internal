function sz = effective_size_rcoda(samples)
%EFFECTIVE_SIZE_RCODA estimate effective sample sizes of each column (calls R-CODA)
%
%     sz = effective_size_rcoda(samples)
%
% This function simply shells R and runs the effectiveSize routine in R-CODA.
%
% Inputs:
%     samples DxN each column is processed in isolation 
%
% Outputs:
%         sz  1xN estimated effective sample size for each column

% It's probably a good idea to have a native Matlab version of this routine.
% But then I would need this routine anyway to test it.

% Iain Murray, September 2009.
% Bugfixed N>8 February 2010.

[D, N] = size(samples);
if (D == 1)
    error('Cannot process "time series" of length 1.');
end

% HACK: This routine only works for small N, because the output file parsing
% below fails if R puts the answers on more than one line. Rather than improve
% the parsing, I quickly bodged in the following fix:
max_N = 5; % (max_N == 8) seems to be ok, but playing safe.
if N > max_N
    sz = [effective_size_rcoda(samples(:, 1:max_N)), ...
            effective_size_rcoda(samples(:, (max_N+1):end))];
    return
end

% The user should put the version of R that they want to use in their system's
% PATH, but if that fails I will try looking in other places too.
Rlocs = {'', '/opt/local/bin/'};
for loc = Rlocs
    [status, output] = system([loc{:}, 'R --version']);
    if status == 0
        R_cmd = [loc{:}, 'R --vanilla CMD BATCH '];
        break;
    end
end
if ~exist('R_cmd')
    error('R executable not found');
end
% TODO cross-platform support for the following is untested. On my linux machine
% I need a clean environment or R fails. I do this with 'env -i'. I don't
% immediately know how to do this on other platforms, but maybe it isn't needed.
if exist('/usr/bin/env', 'file')
    R_cmd = ['/usr/bin/env -i ', R_cmd];
end

% Set up location for temporary files (in RAM if possible)
dirnm = ['esz', sprintf('%d', floor(rand*100000))];
if exist('/dev/shm', 'dir')
    % Linux
    tmp_dir = ['/dev/shm/', dirnm, '/'];
else
    % Should work on all platforms
    tmp_dir = [tempdir(), dirnm, filesep()];
end
success = mkdir(tmp_dir);
assert(success);

% Write samples out to temporary file
save([tmp_dir, 'samples'], 'samples', '-ascii');

% Run R-CODA's routine on that file
R_program = ['library(coda)\n',...
    'mcmcread=read.table("samples")\n',...
    'mcmcrun=cbind(mcmcread)\n',...
    'mcmcobj=mcmc(mcmcrun)\n',...
    'effectiveSize(mcmcobj)\n'];
R_file = [tmp_dir, 'prog.r'];
fid = fopen(R_file, 'w');
fprintf(fid, R_program);
fclose(fid);
out_file = [tmp_dir, 'tmpRout'];
opwd = pwd();
cd(tmp_dir);
system_cmd = [R_cmd, R_file, ' ', out_file];
status = system(system_cmd);
cd(opwd);
assert(~status);

% grab result from output
fid = fopen(out_file);
output = fread(fid);
output = ['a' output(:)'];
fclose(fid);
snippet = output(strfind(output, 'V1'):end);
% FIXME may be Unix specific because of line terminating issues?
idx = strfind(snippet, sprintf('\n'));
snippet = snippet(idx(1)+1:idx(2)-1);
sz = sscanf(snippet, '%f')';

% Delete temporary directory
rmdir(tmp_dir, 's');

