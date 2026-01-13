setup   = setup_synthetic();
max_dim = setup.max_dim;
runs    = setup.runs;

if ~exist('ess_elapsed_time')
  for num_dims = 1:max_dim
    ess_dim(num_dims) = load(sprintf('results/ess_synthetic_%dd', num_dims));
  end
  ess_dim(num_dims+1)   = load(sprintf('results/ess_usps.mat'));
  ess_dim(num_dims+2)   = load(sprintf('results/ess_mine.mat'));
  ess_total_calls       = zeros(runs, max_dim+2);
  ess_effective_samples = zeros(runs, max_dim+2);
  ess_elapsed_time      = zeros(runs, max_dim+2);
  for run=1:runs
    for num_dims=1:12
      ess_total_calls(run, num_dims)       = sum(ess_dim(num_dims).results(run).num_calls);
      ess_effective_samples(run, num_dims) = ess_dim(num_dims).results(run).effective_samples;
      ess_elapsed_time(run, num_dims)      = ess_dim(num_dims).results(run).elapsed;
    end
  end
  clear ess_dim;
  fprintf('Loaded ESS\n');
else
  fprintf('Using loaded ESS\n');
end

if ~exist('lss_elapsed_time')
  for num_dims = 1:max_dim
    lss_dim(num_dims) = load(sprintf('results/lss_synthetic_%dd', num_dims));
  end
  lss_dim(num_dims+1)   = load(sprintf('results/lss_usps.mat'));
  lss_dim(num_dims+2)   = load(sprintf('results/lss_mine.mat'));
  lss_total_calls       = zeros(runs, max_dim+2);
  lss_effective_samples = zeros(runs, max_dim+2);
  lss_elapsed_time      = zeros(runs, max_dim+2);
  for run=1:runs
    for num_dims=1:12
      lss_total_calls(run, num_dims)       = sum(lss_dim(num_dims).results(run).num_calls);
      lss_effective_samples(run, num_dims) = lss_dim(num_dims).results(run).effective_samples;
      lss_elapsed_time(run, num_dims)      = lss_dim(num_dims).results(run).elapsed;
    end
  end
  clear lss_dim;
  fprintf('Loaded LSS\n');
else
  fprintf('Using loaded LSS\n');
end

if ~exist('ur_elapsed_time')
  for num_dims = 1:max_dim
    ur_dim(num_dims) = load(sprintf('results/ur_synthetic_%dd', num_dims));
  end
  ur_dim(num_dims+1)   = load(sprintf('results/ur_usps.mat'));
  ur_dim(num_dims+2)   = load(sprintf('results/ur_mine.mat'));
  ur_total_calls       = zeros(runs, max_dim);
  ur_effective_samples = zeros(runs, max_dim);
  ur_elapsed_time      = zeros(runs, max_dim);
  for run=1:runs
    for num_dims=1:12
      ur_total_calls(run, num_dims)       = sum(ur_dim(num_dims).results(run).num_calls);
      ur_effective_samples(run, num_dims) = ur_dim(num_dims).results(run).effective_samples;
      ur_elapsed_time(run, num_dims)      = ur_dim(num_dims).results(run).elapsed;
    end
  end
  clear ur_dim;
  fprintf('Loaded UR\n');
else
  fprintf('Using loaded UR\n');
end

if ~exist('titsias_elapsed_time')
  for num_dims = 1:max_dim
    titsias_dim(num_dims) = load(sprintf('results/titsias_synthetic_%dd', num_dims));
  end
  titsias_dim(num_dims+1)   = load(sprintf('results/titsias_mine.mat')); % hrm... kill it later.
  titsias_dim(num_dims+2)   = load(sprintf('results/titsias_mine.mat'));
  titsias_total_calls       = zeros(runs, max_dim);
  titsias_effective_samples = zeros(runs, max_dim);
  titsias_elapsed_time      = zeros(runs, max_dim);
  for run=1:runs
    for num_dims=1:12
      titsias_total_calls(run, num_dims)       = sum(titsias_dim(num_dims).results(run).num_calls);
      titsias_effective_samples(run, num_dims) = titsias_dim(num_dims).results(run).effective_samples;
      titsias_elapsed_time(run, num_dims)      = titsias_dim(num_dims).results(run).elapsed;
    end
  end
  clear titsias_dim;
  
  % killing now
  titsias_total_calls(:,11) = 0;
  titsias_effective_samples(:,11) = 0;
  titsias_elapsed_time(:,11) = 0;
  
  fprintf('Loaded Titsias\n');
else
  fprintf('Using loaded Titsias\n');
end

% These determine where the bounds are.
lower_idx = 5;
upper_idx = 96;

fontsize = 8;
set(0, 'DefaultTextInterpreter', 'tex', ...
       'DefaultTextFontName',    'Helvetica', ...
       'DefaultTextFontSize',    fontsize, ...
       'DefaultAxesFontName',    'Helvetica', ...
       'DefaultAxesFontSize',    fontsize);

figure('Units', 'inches', ...
  'Position', [0 0 10 3], ...
  'PaperPositionMode', 'auto');

h_offset = 0.04;
width    = 0.94;
height   = 0.24;
labels   = {'R01', 'R02', 'R03', 'R04', 'R05', 'R06', 'R07', 'R08', 'R09', 'R10', 'USPS', 'Mine' };

if 0
  fwd = @(x) log10(x);
  bwd = @(x) 10.^(x);
else
  fwd = @(x) x;
  bwd = @(x) x;
end

mean_ess_effsamp   = fwd(mean(ess_effective_samples));
sorted_ess_effsamp = sort(ess_effective_samples);
lower_ess_effsamp  = fwd(sorted_ess_effsamp(lower_idx,:));
upper_ess_effsamp  = fwd(sorted_ess_effsamp(upper_idx,:));
stderr_ess_effsamp = std(ess_effective_samples);

mean_lss_effsamp   = fwd(mean(lss_effective_samples));
sorted_lss_effsamp = sort(lss_effective_samples);
lower_lss_effsamp  = fwd(sorted_lss_effsamp(lower_idx,:));
upper_lss_effsamp  = fwd(sorted_lss_effsamp(upper_idx,:));
stderr_lss_effsamp = std(lss_effective_samples);

mean_ur_effsamp   = fwd(mean(ur_effective_samples));
sorted_ur_effsamp = sort(ur_effective_samples);
lower_ur_effsamp  = fwd(sorted_ur_effsamp(lower_idx,:));
upper_ur_effsamp  = fwd(sorted_ur_effsamp(upper_idx,:));
stderr_ur_effsamp = std(ur_effective_samples);

mean_titsias_effsamp   = fwd(mean(titsias_effective_samples));
sorted_titsias_effsamp = sort(titsias_effective_samples);
lower_titsias_effsamp  = fwd(sorted_titsias_effsamp(lower_idx,:));
upper_titsias_effsamp  = fwd(sorted_titsias_effsamp(upper_idx,:));
lower_titsias_effsamp(~isfinite(lower_titsias_effsamp)) = 0;
stderr_titsias_effsamp = std(titsias_effective_samples);

mean_ess_eltime   = fwd(mean(ess_elapsed_time));
sorted_ess_eltime = sort(ess_elapsed_time);
lower_ess_eltime  = fwd(sorted_ess_eltime(lower_idx,:));
upper_ess_eltime  = fwd(sorted_ess_eltime(upper_idx,:));
stderr_ess_eltime = std(ess_elapsed_time);

mean_lss_eltime   = fwd(mean(lss_elapsed_time));
sorted_lss_eltime = sort(lss_elapsed_time);
lower_lss_eltime  = fwd(sorted_lss_eltime(lower_idx,:));
upper_lss_eltime  = fwd(sorted_lss_eltime(upper_idx,:));
stderr_lss_eltime = std(lss_elapsed_time);

mean_ur_eltime   = fwd(mean(ur_elapsed_time));
sorted_ur_eltime = sort(ur_elapsed_time);
lower_ur_eltime  = fwd(sorted_ur_eltime(lower_idx,:));
upper_ur_eltime  = fwd(sorted_ur_eltime(upper_idx,:));
stderr_ur_eltime = std(ur_elapsed_time);

mean_titsias_eltime   = fwd(mean(titsias_elapsed_time));
sorted_titsias_eltime = sort(titsias_elapsed_time);
lower_titsias_eltime  = fwd(sorted_titsias_eltime(lower_idx,:));
upper_titsias_eltime  = fwd(sorted_titsias_eltime(upper_idx,:));
stderr_titsias_eltime = std(titsias_elapsed_time);

mean_ess_totcalls   = fwd(mean(ess_total_calls));
sorted_ess_totcalls = sort(ess_total_calls);
lower_ess_totcalls  = fwd(sorted_ess_totcalls(lower_idx,:));
upper_ess_totcalls  = fwd(sorted_ess_totcalls(upper_idx,:));
stderr_ess_totcalls = std(ess_total_calls);

mean_lss_totcalls   = fwd(mean(lss_total_calls));
sorted_lss_totcalls = sort(lss_total_calls);
lower_lss_totcalls  = fwd(sorted_lss_totcalls(lower_idx,:));
upper_lss_totcalls  = fwd(sorted_lss_totcalls(upper_idx,:));
stderr_lss_totcalls = std(lss_total_calls);

mean_ur_totcalls   = fwd(mean(ur_total_calls));
sorted_ur_totcalls = sort(ur_total_calls);
lower_ur_totcalls  = fwd(sorted_ur_totcalls(lower_idx,:));
upper_ur_totcalls  = fwd(sorted_ur_totcalls(upper_idx,:));
stderr_ur_totcalls = std(ur_total_calls);

mean_titsias_totcalls   = fwd(mean(titsias_total_calls));
sorted_titsias_totcalls = sort(titsias_total_calls);
lower_titsias_totcalls  = fwd(sorted_titsias_totcalls(lower_idx,:));
upper_titsias_totcalls  = fwd(sorted_titsias_totcalls(upper_idx,:));
stderr_titsias_totcalls = std(titsias_total_calls);

subplot('Position', [h_offset 0.72 width height]);
b = bar([1:12], bsxfun(@rdivide, [mean_ess_effsamp ; mean_lss_effsamp ; mean_ur_effsamp ; mean_titsias_effsamp]', mean_ess_effsamp'));
c = get(b,'Children');

xdata = zeros([12 4]);
ydata = zeros([12 4]);
for i = 1:length(c)
  xdata(:,i) = mean(get(c{i},'xdata'));
  tempYData  = get(c{i},'ydata');
  ydata(:,i) = mean(tempYData(2:3,:))';
end

hold on;
%e = errorbar(xdata, ydata, ydata- ...
%  bsxfun(@rdivide, [lower_ess_effsamp ; lower_lss_effsamp ; lower_ur_effsamp ; lower_titsias_effsamp]', mean_ess_effsamp'), ...
%  bsxfun(@rdivide, [upper_ess_effsamp ; upper_lss_effsamp ; upper_ur_effsamp ; upper_titsias_effsamp]', mean_ess_effsamp') - ydata, 'k.');
e = errorbar(xdata, ydata, bsxfun(@rdivide, [stderr_ess_effsamp ; stderr_lss_effsamp ; stderr_ur_effsamp ; stderr_titsias_effsamp]', mean_ess_effsamp'), 'k.');
hold off;
%xlabel('Number of Dimensions');
ylabel('Effective Samples');
xlim([0.5 12.5]);
ylim([0 4]);
set(gca, 'Box', 'off');
set(gca, 'YTick', [0:4]);
set(gca, 'YTickLabel', sprintf('%0.1g|', get(gca, 'YTick')));
set(gca, 'XTickLabel', sprintf('x%0.0f|', mean_ess_effsamp));
set(gca, 'TickLength', get(gca, 'TickLength')/2);

h = legend('Elliptical Slice', 'Line Slice', ['Neal ' ...
                    , 'M-H'], 'Control Point M-H', ...
                    'Location', 'NorthOutside', 'Orientation', 'horizontal');    
legend boxoff;
set(h, 'FontSize', 6);
set(h, 'Position', [0.2 0.9 0.4 0.1]);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                  
subplot('Position', [h_offset 0.42 width height]);
b = bar([1:12], bsxfun(@rdivide, [mean_ess_eltime ; mean_lss_eltime ; mean_ur_eltime ; mean_titsias_eltime]', mean_ess_eltime'));
c = get(b,'Children');

xdata = zeros([12 4]);
ydata = zeros([12 4]);
for i = 1:length(c)
  xdata(:,i) = mean(get(c{i},'xdata'));
  tempYData  = get(c{i},'ydata');
  ydata(:,i) = mean(tempYData(2:3,:))';
end

hold on;
%e = errorbar(xdata, ydata, ydata- ...
%  bsxfun(@rdivide, [lower_ess_eltime ; lower_lss_eltime ; lower_ur_eltime ; lower_titsias_eltime]', mean_ess_eltime'), ...
%  bsxfun(@rdivide, [upper_ess_eltime ; upper_lss_eltime ; upper_ur_eltime ; upper_titsias_eltime]', mean_ess_eltime') - ydata, 'k.');
e = errorbar(xdata, ydata, bsxfun(@rdivide, [stderr_ess_eltime ; stderr_lss_eltime ; stderr_ur_eltime ; stderr_titsias_eltime]', mean_ess_eltime'), 'k.');
hold off;
%xlabel('Number of Dimensions');
ylabel('CPU Time');
xlim([0.5 12.5]);
set(gca, 'YTick', [0:5]);
set(gca, 'Box', 'off');
set(gca, 'YTickLabel', sprintf('%0.1g|', get(gca, 'YTick')));
set(gca, 'XTickLabel', sprintf('x%0.0f|', mean_ess_eltime));
set(gca, 'TickLength', get(gca, 'TickLength')/2);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

subplot('Position', [h_offset 0.12 width height]);
b = bar([1:12], [mean_ess_totcalls ; mean_lss_totcalls ; mean_ur_totcalls ; mean_titsias_totcalls]'/1000000);
c = get(b,'Children');

xdata = zeros([12 4]);
ydata = zeros([12 4]);
for i = 1:length(c)
  xdata(:,i) = mean(get(c{i},'xdata'));
  tempYData  = get(c{i},'ydata');
  ydata(:,i) = mean(tempYData(2:3,:))';
end

hold on;
%e = errorbar(xdata, ydata, ydata-[lower_ess_totcalls ; lower_lss_totcalls ; lower_ur_totcalls ; lower_titsias_totcalls]'/1000000, ...
%             [upper_ess_totcalls ; upper_lss_totcalls ; upper_ur_totcalls ; ...
%             upper_titsias_totcalls]'/1000000-ydata, 'k.');
e = errorbar(xdata, ydata, [stderr_ess_totcalls ; stderr_lss_totcalls ; stderr_ur_totcalls ; stderr_titsias_totcalls]'/1000000, 'k.');
hold off;
xlim([0.5 12.5]);
xlabel('Experiment');
ylabel('Lhood Evals (M)');
set(gca, 'Box', 'off');
set(gca, 'YTickLabel', sprintf('%0.1g|', get(gca, 'YTick')));
set(gca, 'XTickLabel', labels);
set(gca, 'TickLength', get(gca, 'TickLength')/2);

%print -depsc -r600 'plots/bars.eps';
%close;

im_hatch = applyhatch_pluscolor(gcf,'\-x.', 0);
imwrite(im_hatch,'plots/bars.png', 'png')
system('convert plots/bars.png plots/bars.eps');

