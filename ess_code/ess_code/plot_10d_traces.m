clear
figure(1); clf ; hold on;

addpath('results');

run = 1;

load titsias_synthetic_10d.mat
num_control = round(results(run).num_calls / length(results(run).loglikes));
num_show = 10000;
load titsias_synthetic_10d
subplot(1, 2, 1);
its = 1:floor(num_show/num_control);
plot(its*num_control, results(run).loglikes(its));
xlabel('# Control variable moves');
ylabel('log L');
title('Control Variables');
ax = axis;

load ess_synthetic_1d
subplot(1, 2, 2);
its = 1:num_control:num_show;
plot(its, results(run).loglikes(its));
xlabel('# Iterations');
title('Elliptical slice sampling');
ax2 = axis;
new_ax = ax;
y_mx = max(ax(4), ax2(4));
y_mn = min(ax(3), ax2(3));
new_ax(3:4) = [y_mn, y_mx];
axis(new_ax);
subplot(1, 2, 1);
axis(new_ax);

figname = 'plots/traces10d';
set(gcf, 'PaperPosition', [0 0 5 1.5]);
print([figname, '.eps'], '-depsc');
system(['epstopdf ' figname, '.eps']);
close;
