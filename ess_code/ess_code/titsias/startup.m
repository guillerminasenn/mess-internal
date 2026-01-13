% This startup file added by Iain Murray

% run usual startup script
startups = which('startup', '-ALL');
if length(startups) > 1
    run(startups{2})
end
 
% Add toolbox to the Matlab path (if required)
if ~exist('gaussianConditionalDisplay')
    addpath('toolbox');
end 

clear startups ans
