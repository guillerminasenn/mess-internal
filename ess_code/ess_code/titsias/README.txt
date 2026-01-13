
Software on sampling in Gaussian processes using control variables. 
See the following publication: 

M. K. Titsias, N.D. Lawrence and M. Rattray.
Efficient Sampling for Gaussian Process Inference using Control Variables.
Advances in Neural Information Processing Systems, 2009. 

Release version v1.0. 

Release date: 17-Feb-2010

Supported features: The covariance function supported in only the rbf and 
the ARD kernel. Supported likelihood models include  probit, logit (for binary 
classification) and  Poisson regression for counts data. 

External software needed: You need to obtain the minimize.m function of 
Carl Edward Rasmussen available from 
http://www.kyb.tuebingen.mpg.de/bs/people/carl/code/minimize/

This is the first (very basic) version of the software, Next version will include      
more covariance functions, alternative MCMC algorithms (such Gibbs sampling) and 
more applications.  
 
Acknowledgements: Thanks to Iain Murray for speeding up the function
gpsampControlTrain.m.

This software is freely available for academic use only. You 
should not distribute this software without having first my permission.  

Michalis Titsias   
