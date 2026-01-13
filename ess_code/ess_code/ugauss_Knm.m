function K = ugauss_Knm(x1, x2)
%UGAUSS_KNM produce NxM unit Gaussian kernel matrix for DxN and DxM inputs
%
% Inputs:
%      x1 DxN 
%      x2 DxM (optional, default: x2 = x1)
%
% Outputs:
%      K  NxM covariance matrix

% Iain Murray, March 2008

if nargin == 1
    x2 = x1; % Caching sum(x1.*x1,1) doesn't make a practical difference
end

K = exp(bsxfun(@minus, bsxfun(@minus, x1'*(2*x2), sum(x1.*x1,1)'), sum(x2.*x2,1)));

% What a difference a misplaced bracket can make! (time x1.5 for N=20000, D=21)!!
%K = exp(bsxfun(@minus, bsxfun(@minus, 2*(x1'*x2), sum(x1.*x1,1)'), sum(x2.*x2,1)));

% Also slower:
%K = exp(x1'*(2*x2) - bsxfun(@plus, sum(x1.*x1,1)', sum(x2.*x2,1)));

