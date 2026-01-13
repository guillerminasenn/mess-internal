function setup = setup_usps()
% This is shared across all of the usps experiments.

addpath('titsias');
addpath('titsias/toolbox');

[setup.x_train setup.y_train setup.x_test setup.y_test] = loadBinaryUSPS(3, 5);
setup.runs        = 100;
setup.iterations  = 100000;
setup.burn        = 10000;

[n D] = size(setup.x_train);

% Set up Michalis' code so we can just use his covariance matrix.
setup.options                       = gpsampOptions('classification'); 
setup.options.constraints.likHyper  = 'fixed';
setup.options.constraints.kernHyper = 'fixed';
setup.model                         = gpsampCreate(setup.y_train(:), setup.x_train, setup.options);
%setup.log_ell                       = 2.5204;
%setup.log_sigstd                    = 5.1261;
setup.log_ell                       = 2.5;
setup.log_sigstd                    = 3.5;
setup.model.GP.logtheta             = [repmat(2*setup.log_ell,1,D), 2*setup.log_sigstd];
setup.K                             = kernCompute(setup.model.GP, setup.x_train);
