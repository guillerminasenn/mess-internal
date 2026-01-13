function [xx, cur_log_like] = gppu_underrelax(step_size, xx, chol_Sigma, log_like_fn, cur_log_like)
%GPPU_UNDERRELAX Gaussian prior posterior update - using "under-relaxation"
%
%     [xx, cur_log_like] = gppu_underrelax(step_size, xx, chol_Sigma, log_like_fn[, cur_log_like])
%
% A Dx1 vector xx with prior N(0,Sigma) is updated leaving the posterior
% distribution invariant.
%
% Inputs:
%       step_size 1x1 small values => small moves, but higher acceptance rates
%              xx Dx1 initial vector
%      chol_Sigma DxD chol(Sigma). Sigma is the prior covariance of xx
%     log_like_fn @fn log_like_fn(xx) returns 1x1 log likelihood
%    cur_log_like 1x1 Optional: log_like_fn(xx) of initial vector
%
% Outputs:
%              xx Dx1 perturbed vector with posterior left stationary.
%    cur_log_like 1x1 log_like_fn(xx) of final vector
%
% See also: GPPU_LINESLICE, GPPU_ELLIPTICAL

% Iain Murray, August 2009

assert(isvector(xx));
xx = xx(:);
D = length(xx);

if ~exist('cur_log_like', 'var') || isempty(cur_log_like)
    cur_log_like = log_like_fn(xx);
end

x_prop = sqrt(1-step_size*step_size)*xx + step_size*(chol_Sigma'*randn(D, 1));
prop_log_like = log_like_fn(x_prop);
if log(rand) < (prop_log_like - cur_log_like)
    xx = x_prop;
    cur_log_like = prop_log_like;
end
