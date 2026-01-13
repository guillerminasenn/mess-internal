function [xx, cur_log_like] = gppu_lineslice(xx, chol_Sigma, log_like_fn, cur_log_like)
%GPPU_LINESLICE Gaussian prior posterior update by slice sampling along line ~ prior
%
%     [xx, cur_log_like] = gppu_lineslice(xx, chol_Sigma, log_like_fn[, cur_log_like])
%
% A Dx1 vector xx with prior N(0,Sigma) is updated leaving the posterior
% distribution invariant.
%
% Inputs:
%              xx Dx1 initial vector
%      chol_Sigma DxD chol(Sigma). Sigma is the prior covariance of xx
%     log_like_fn @fn log_like_fn(xx) returns 1x1 log likelihood
%    cur_log_like 1x1 Optional: log_like_fn(xx) of initial vector
%
% Outputs:
%              xx Dx1 perturbed vector with posterior left stationary.
%    cur_log_like 1x1 log_like_fn(xx) of final vector
%
% See also: GPPU_UNDERRELAX, GPPU_ELLIPTICAL

% Iain Murray, August 2009

assert(isvector(xx));
xx = xx(:);
D = length(xx);

if ~exist('cur_log_like', 'var') || isempty(cur_log_like)
    cur_log_like = log_like_fn(xx);
end

% Slice sample along this random direction:
direction = chol_Sigma'*randn(D, 1);

% Moves don't respect detailed balance wrt prior, so we need to evaluate the
% change in prior. This requires some extra O(D^2) operations for the following
% cached quantities:
invSigDir = solve_chol(chol_Sigma, direction); % from Carl's GPML toolbox
lp_cf1 = -xx'*invSigDir;
lp_cf2 = -0.5*direction'*invSigDir;

% Slice sample along line through xx and along direction
start_width = 1;
w_min = -start_width*rand;
w_max = w_min + start_width;
hh = log(rand) + cur_log_like;
while true
    % Propose and evaluate a new point
    w_prop = rand*(w_max - w_min) + w_min;
    x_prop = xx + (w_prop * direction);
    prop_log_like = log_like_fn(x_prop);
    prop_log_prior = w_prop*(lp_cf1 + w_prop*lp_cf2);
    if (prop_log_like + prop_log_prior) > hh
        % New point is on slice, ** accept and exit loop **
        xx = x_prop;
        cur_log_like = prop_log_like;
        break;
    end
    % Sanity checking:
    if w_prop == 0
        error('BUG DETECTED: Shrunk to current position and still not acceptable.');
    end
    % Shrink slice to rejected point
    if w_prop > 0
        w_max = w_prop;
    else
        w_min = w_prop;
    end
end

