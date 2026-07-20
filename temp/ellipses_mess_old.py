import os
import sys
import numpy as np
import matplotlib.pyplot as plt

repo_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
src_path = os.path.join(repo_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from mess.problems.advection_diffusion import (
    make_omegas_power,
    make_Astar_nn,
    make_Astar_from_atrue,
    params_from_skew,
    prior_diag_from_powerlaw,
    solve_theta,
    AdvectionDiffusionToy,
 )
from mess.algorithms.mess import mess_step

# Configuration
seed_data = 0
seed_mcmc = 0
n_iters = 20000
burn_in = 10000
M = 5

d = 10
d_max = 100

# Data hyperparameters
kappa = 0.02
sigma = 0.5
alpha = 3
gamma = 2
tau2 = 2.0
a_mode = 'nearest_neighbor'
use_prior_A = True
shared_draws_seed = seed_data

# Observation configuration
obs_highest_freq = 6
obs_bandwidth = 3
obs_config = 'central_modes'

datasets_by_dim = {}

def get_obs_indices(dim_value, highest_freq, bandwidth):
    highest_freq = min(highest_freq, dim_value)
    bandwidth = min(bandwidth, dim_value)
    start = max(0, highest_freq - bandwidth + 1)
    return np.arange(start, highest_freq + 1, dtype=int)

def get_param_indices_for_dim(dim_value, shared_draws):
    cache = shared_draws.setdefault('param_indices_cache', {})
    if dim_value not in cache:
        iju = shared_draws['param_iju']
        mask = (iju[0] < dim_value) & (iju[1] < dim_value)
        cache[dim_value] = np.nonzero(mask)[0]
    return cache[dim_value]

def build_shared_draws(d_max, kappa, sigma, alpha, gamma, tau2, offset, a_mode, seed):
    rng = np.random.default_rng(seed)
    m_max = d_max * (d_max - 1) // 2
    prior_diag_max = prior_diag_from_powerlaw(d_max, alpha=alpha, gamma=gamma, tau2=tau2, offset=offset)
    if prior_diag_max.shape != (m_max,):
        raise ValueError(f'prior_diag_max must have shape ({m_max},), got {prior_diag_max.shape}')
    if a_mode == 'nearest_neighbor':
        omegas = make_omegas_power(d_max, beta=alpha, c=2.0 ** (-gamma), offset=offset)
        A_true_max = make_Astar_nn(d_max, omegas)
        a_true_max = params_from_skew(A_true_max)
    elif a_mode == 'prior':
        z_prior = rng.standard_normal(m_max)
        a_true_max = z_prior * np.sqrt(prior_diag_max)
        A_true_max = make_Astar_from_atrue(d_max, a_true_max)
    else:
        raise ValueError('a_mode must be nearest_neighbor or prior')
    g_max = np.zeros(d_max, dtype=float)
    g_max[0] = 1.0
    theta_true_max = solve_theta(d_max, a_true_max, g_max, kappa)
    noise_max = rng.standard_normal(d_max)
    z_init = rng.standard_normal(m_max)
    a_init_max = z_init * np.sqrt(prior_diag_max)
    return {
        'd_max': d_max,
        'm_max': m_max,
        'kappa': kappa,
        'sigma': sigma,
        'alpha': alpha,
        'gamma': gamma,
        'tau2': tau2,
        'offset': offset,
        'a_mode': a_mode,
        'param_iju': np.triu_indices(d_max, k=1),
        'param_indices_cache': {},
        'prior_diag': prior_diag_max,
        'a_true': a_true_max,
        'A_true': A_true_max,
        'g': g_max,
        'theta_true': theta_true_max,
        'noise': noise_max,
        'a_init': a_init_max,
    }

def generate_advection_diffusion_data_shared(dim_value, obs_indices, shared_draws):
    a_mode_local = shared_draws['a_mode']
    param_idx = get_param_indices_for_dim(dim_value, shared_draws)
    prior_diag = shared_draws['prior_diag'][param_idx]
    g = shared_draws['g'][:dim_value]
    if a_mode_local == 'nearest_neighbor':
        omegas = make_omegas_power(
            dim_value,
            beta=shared_draws['alpha'],
            c=2.0 ** (-shared_draws['gamma']),
            offset=shared_draws['offset'],
        )
        A_true = make_Astar_nn(dim_value, omegas)
        a_true = params_from_skew(A_true)
        theta_true = solve_theta(dim_value, a_true, g, shared_draws['kappa'])
    elif a_mode_local == 'prior':
        a_true = shared_draws['a_true'][param_idx]
        A_true = make_Astar_from_atrue(dim_value, a_true)
        theta_true = shared_draws['theta_true'][:dim_value]
    else:
        raise ValueError('a_mode must be nearest_neighbor or prior')
    noise = shared_draws['noise'][:dim_value]
    y = theta_true[obs_indices] + shared_draws['sigma'] * noise[obs_indices]
    a_init = shared_draws['a_init'][param_idx]
    return {
        'dim': dim_value,
        'kappa': shared_draws['kappa'],
        'alpha': shared_draws['alpha'],
        'gamma': shared_draws['gamma'],
        'tau2': shared_draws['tau2'],
        'sigma': shared_draws['sigma'],
        'obs_indices': obs_indices,
        'prior_diag': prior_diag,
        'a_true': a_true,
        'A_true': A_true,
        'g': g,
        'theta_true': theta_true,
        'y': y,
        'a_init': a_init,
    }

def get_dataset_for_dim(d_value, seed=0):
    if d_value in datasets_by_dim:
        return datasets_by_dim[d_value]
    obs_indices = get_obs_indices(d_value, obs_highest_freq, obs_bandwidth)
    data = generate_advection_diffusion_data_shared(d_value, obs_indices, shared_draws)
    data['obs_indices'] = obs_indices
    datasets_by_dim[d_value] = data
    return data

def build_problem_for_dim(d_value, seed=0):
    data = get_dataset_for_dim(d_value, seed=seed)
    obs_indices = data['obs_indices']
    problem = AdvectionDiffusionToy(
        dim=d_value,
        kappa=kappa,
        sigma=sigma,
        y=data['y'],
        obs_indices=obs_indices,
        g=data['g'],
        prior_diag=data['prior_diag'],
    )
    return problem, data['a_init'], obs_indices, data

shared_draws = build_shared_draws(
    d_max=d_max,
    kappa=kappa,
    sigma=sigma,
    alpha=alpha,
    gamma=gamma,
    tau2=tau2,
    offset=1.0,
    a_mode='prior' if use_prior_A else a_mode,
    seed=shared_draws_seed
)

def mess_step_with_trace(x, problem, rng, M=5):
    prior_mean = problem.prior_mean()
    x_centered = x - prior_mean
    nu_centered = problem.sample_prior(rng) - prior_mean
    logy = problem.log_likelihood(x) + np.log(rng.uniform())
    alpha_val = rng.uniform(0, 2 * np.pi)
    phi_min = 0.0
    phi_max = 2 * np.pi
    intervals = []
    while True:
        phi_vector = rng.uniform(phi_min, phi_max, size=M)
        x_prop_vector = (
            prior_mean[:, np.newaxis]
            + np.cos(phi_vector - alpha_val) * x_centered[:, np.newaxis]
            + np.sin(phi_vector - alpha_val) * nu_centered[:, np.newaxis]
        )
        log_likelihoods = np.array([
            problem.log_likelihood(x_prop_vector[:, i])
            for i in range(M)
        ])
        valid_indices = np.where(log_likelihoods > logy)[0]
        intervals.append({
            'phi_min': float(phi_min),
            'phi_max': float(phi_max),
            'phi_vector': phi_vector.copy(),
            'log_likelihoods': log_likelihoods.copy(),
            'valid_indices': valid_indices.copy(),
        })
        if len(valid_indices) > 0:
            accepted_index = int(rng.choice(valid_indices))
            accepted_phi = float(phi_vector[accepted_index])
            x_new = x_prop_vector[:, accepted_index]
            trace = {
                'x': x.copy(),
                'x_centered': x_centered.copy(),
                'nu_centered': nu_centered.copy(),
                'alpha': float(alpha_val),
                'logy': float(logy),
                'intervals': intervals,
                'accepted_phi': accepted_phi,
                'accepted_interval_index': len(intervals) - 1,
                'accepted_index': accepted_index,
            }
            return x_new, trace
        phi_min = np.max(np.concatenate([np.array([phi_min]), phi_vector[phi_vector < alpha_val]]))
        phi_max = np.min(np.concatenate([np.array([phi_max]), phi_vector[phi_vector >= alpha_val]]))


def _format_angles(vals):
    return np.array2string(np.asarray(vals), precision=3, separator=', ', suppress_small=True)


problem, x0, obs_indices, data = build_problem_for_dim(d, seed=seed_data)
rng = np.random.default_rng(seed_mcmc)

base_iters = list(range(10000, 10006))
extra_iters = [9998, 10011]
target_iters = sorted(set(base_iters + extra_iters))
traces_by_iter = {}

x = x0.copy()
trace = None
for it in range(1, n_iters + 1):
    if it in target_iters:
        x, trace_it = mess_step_with_trace(x, problem, rng, M=M)
        traces_by_iter[it] = trace_it
        trace = trace_it
    else:
        x, _, _ = mess_step(x, problem, rng, M=M, use_lp=False)

for it in target_iters:
    trace_it = traces_by_iter.get(it)
    if trace_it is None:
        print(f'Iteration {it}: missing trace')
        continue
    print(f'\nIteration {it}')
    print(f"  alpha = {trace_it['alpha']:.6f}")
    for s_idx, interval in enumerate(trace_it['intervals'], start=1):
        print(f"  subiter {s_idx}: phi_min = {interval['phi_min']:.6f}, phi_max = {interval['phi_max']:.6f}")
        print(f"    angles = {_format_angles(interval['phi_vector'])}")
    print(f"  accepted_phi = {trace_it['accepted_phi']:.6f} (interval {trace_it['accepted_interval_index'] + 1})")

if trace is None:
    raise RuntimeError('Trace was not captured; check iteration settings.')
print('\nCaptured iteration for plotting:', target_iters[0])

def build_plane_basis(x_centered, nu_centered):
    x_norm = np.linalg.norm(x_centered)
    if x_norm == 0:
        raise ValueError('Current state has zero norm; cannot define ellipse plane.')
    u = x_centered / x_norm
    nu_parallel = float(np.dot(u, nu_centered))
    v_perp = nu_centered - nu_parallel * u
    v_perp_norm = np.linalg.norm(v_perp)
    if v_perp_norm == 0:
        # Fallback: pick an arbitrary perpendicular direction
        basis = np.zeros_like(u)
        basis[0] = 1.0
        if np.abs(np.dot(basis, u)) > 0.9:
            basis[1] = 1.0
            basis[0] = 0.0
        v_perp = basis - np.dot(basis, u) * u
        v_perp_norm = np.linalg.norm(v_perp)
    w = v_perp / v_perp_norm
    return u, w, x_norm, nu_parallel, v_perp_norm


def ellipse_coords(phi, alpha_val, x_norm, nu_parallel, nu_perp_norm):
    delta = phi - alpha_val
    x_coord = x_norm * np.cos(delta) + nu_parallel * np.sin(delta)
    y_coord = nu_perp_norm * np.sin(delta)
    return x_coord, y_coord


def draw_base_ellipse(ax, phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm, color='0.25'):
    xs, ys = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.plot(xs, ys, color=color, linewidth=1.2)
    ax.axhline(0.0, color='0.85', linewidth=0.8)
    ax.axvline(0.0, color='0.85', linewidth=0.8)
    ax.set_aspect('equal', adjustable='box')
    return xs, ys


def _label_offset(x, y, base=14):
    dx = base if x >= 0 else -base
    dy = base if y >= 0 else -base
    return dx, dy


def _half_arrow_label(ax, x_end, y_end, text, offset=8):
    mid = np.array([0.5 * x_end, 0.5 * y_end], dtype=float)
    normal = np.array([-y_end, x_end], dtype=float)
    norm_len = np.linalg.norm(normal)
    if norm_len == 0:
        dx, dy = 0.0, 0.0
    else:
        normal /= norm_len
        dx, dy = normal * offset
    ax.annotate(text, xy=(mid[0], mid[1]), xytext=(dx, dy), textcoords='offset points', color='black')


def annotate_angles(ax, alpha_val, x_norm, nu_parallel, nu_perp_norm):
    x0, y0 = ellipse_coords(alpha_val, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.scatter([x0], [y0], color='black', s=30, zorder=6)
    ax.annotate(r'$\alpha$', xy=(x0, y0), xytext=(6, 6), textcoords='offset points', color='black')

    v_phi = alpha_val + 0.5 * np.pi
    xv, yv = ellipse_coords(v_phi, alpha_val, x_norm, nu_parallel, nu_perp_norm)

    ax.annotate('', xy=(x0, y0), xytext=(0.0, 0.0),
                arrowprops={'arrowstyle': '->', 'color': 'black', 'linewidth': 1.5})
    ax.annotate('', xy=(xv, yv), xytext=(0.0, 0.0),
                arrowprops={'arrowstyle': '->', 'color': 'black', 'linewidth': 1.5})
    _half_arrow_label(ax, x0, y0, 'x', offset=8)
    _half_arrow_label(ax, xv, yv, 'v', offset=8)

    # Place 0 at phi=0 (alpha radians clockwise from the x point)
    xz, yz = ellipse_coords(0.0, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    dzx, dzy = _label_offset(xz, yz, base=12)
    ax.annotate('0', xy=(xz, yz), xytext=(dzx, dzy), textcoords='offset points', color='0.2')
    ax.annotate('2pi', xy=(xz, yz), xytext=(dzx + 18, dzy - 18), textcoords='offset points', color='0.2')


def plot_angle_markers(ax, phi_vector, alpha_val, x_norm, nu_parallel, nu_perp_norm, color='tab:red', marker='o'):
    xs, ys = ellipse_coords(phi_vector, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.scatter(xs, ys, color=color, s=35, marker=marker, zorder=6)
    return xs, ys


def plot_slice_segment(ax, phi_grid, mask, alpha_val, x_norm, nu_parallel, nu_perp_norm, color='green', alpha=0.5, linewidth=5.0):
    mask = np.asarray(mask, dtype=bool)
    if mask[0] and mask[-1]:
        phi_ext = np.concatenate([phi_grid, phi_grid[1:] + 2 * np.pi])
        mask_ext = np.concatenate([mask, mask[1:]])
        xs, ys = ellipse_coords(phi_ext, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        xs = xs.copy()
        ys = ys.copy()
        xs[~mask_ext] = np.nan
        ys[~mask_ext] = np.nan
        ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)
        return
    xs, ys = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    xs = xs.copy()
    ys = ys.copy()
    xs[~mask] = np.nan
    ys[~mask] = np.nan
    ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)


def draw_interval_brackets(ax, phi_min, phi_max, alpha_val, x_norm, nu_parallel, nu_perp_norm, bracket_len, color='orange', linewidth=1.0, alpha=1.0):
    for phi in (phi_min, phi_max):
        x0, y0 = ellipse_coords(phi, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        delta = phi - alpha_val
        dx = -x_norm * np.sin(delta) + nu_parallel * np.cos(delta)
        dy = nu_perp_norm * np.cos(delta)
        normal = np.array([-dy, dx], dtype=float)
        norm_len = np.linalg.norm(normal)
        if norm_len == 0:
            continue
        normal /= norm_len
        x1 = x0 - 0.5 * bracket_len * normal[0]
        y1 = y0 - 0.5 * bracket_len * normal[1]
        x2 = x0 + 0.5 * bracket_len * normal[0]
        y2 = y0 + 0.5 * bracket_len * normal[1]
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=linewidth, alpha=alpha)


def draw_interval_arc(ax, phi_min, phi_max, alpha_val, x_norm, nu_parallel, nu_perp_norm, color='orange', linewidth=3.0, alpha=0.2):
    if phi_min <= phi_max:
        phi_arc = np.linspace(phi_min, phi_max, 200)
    else:
        phi_arc = np.concatenate([
            np.linspace(phi_min, 2 * np.pi, 150),
            np.linspace(0.0, phi_max, 150),
        ])
    xs, ys = ellipse_coords(phi_arc, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.plot(xs, ys, color=color, linewidth=linewidth, linestyle='--', alpha=alpha)


def plot_trace(trace_item, title_prefix):
    x_centered = trace_item['x_centered']
    nu_centered = trace_item['nu_centered']
    alpha_val = trace_item['alpha']
    intervals = trace_item['intervals']
    accepted_phi = trace_item['accepted_phi']
    accepted_interval_idx = trace_item['accepted_interval_index']
    logy = trace_item['logy']

    u, w, x_norm, nu_parallel, nu_perp_norm = build_plane_basis(x_centered, nu_centered)
    phi_grid = np.linspace(0.0, 2 * np.pi, 600)

    ellipse_props = (
        problem.prior_mean()[:, np.newaxis]
        + np.cos(phi_grid - alpha_val) * x_centered[:, np.newaxis]
        + np.sin(phi_grid - alpha_val) * nu_centered[:, np.newaxis]
    )
    log_likes_grid = np.array([problem.log_likelihood(ellipse_props[:, i]) for i in range(phi_grid.size)])
    slice_mask = log_likes_grid > logy

    xs_all, ys_all = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    pad = 0.08
    xlim = (xs_all.min() * (1 + pad), xs_all.max() * (1 + pad))
    ylim = (ys_all.min() * (1 + pad), ys_all.max() * (1 + pad))
    bracket_len = 0.05 * max(xs_all.max() - xs_all.min(), ys_all.max() - ys_all.min())

    n_base_panels = 1
    n_interval_panels = len(intervals)
    n_panels = n_base_panels + n_interval_panels
    n_cols = 3
    n_rows = int(np.ceil(n_panels / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(13, 4 * n_rows), constrained_layout=True)
    axes = np.array(axes).reshape(-1)

    panel_idx = 0
    ax = axes[panel_idx]
    draw_base_ellipse(ax, phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    plot_slice_segment(ax, phi_grid, slice_mask, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    draw_interval_arc(ax, 0.0, 2 * np.pi, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    draw_interval_brackets(ax, 0.0, 2 * np.pi, alpha_val, x_norm, nu_parallel, nu_perp_norm, bracket_len)
    annotate_angles(ax, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.set_title(f'{title_prefix}: full bracket')
    panel_idx += 1

    for idx, interval in enumerate(intervals):
        ax = axes[panel_idx]
        draw_base_ellipse(ax, phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        plot_slice_segment(ax, phi_grid, slice_mask, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        draw_interval_arc(
            ax,
            interval['phi_min'],
            interval['phi_max'],
            alpha_val,
            x_norm,
            nu_parallel,
            nu_perp_norm,
        )
        draw_interval_brackets(
            ax,
            interval['phi_min'],
            interval['phi_max'],
            alpha_val,
            x_norm,
            nu_parallel,
            nu_perp_norm,
            bracket_len,
        )
        annotate_angles(ax, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        plot_angle_markers(
            ax,
            interval['phi_vector'],
            alpha_val,
            x_norm,
            nu_parallel,
            nu_perp_norm,
            color='tab:red',
        )
        if idx == accepted_interval_idx:
            valid_indices = interval['valid_indices']
            if valid_indices.size > 0:
                plot_angle_markers(
                    ax,
                    interval['phi_vector'][valid_indices],
                    alpha_val,
                    x_norm,
                    nu_parallel,
                    nu_perp_norm,
                    color='tab:green',
                )
            xa, ya = ellipse_coords(accepted_phi, alpha_val, x_norm, nu_parallel, nu_perp_norm)
            ax.scatter([xa], [ya], facecolors='none', edgecolors='darkgreen', s=150, marker='s', linewidths=2.0)
            ax.set_title(f'Interval {idx + 1}: accepted')
        else:
            ax.set_title(f'Interval {idx + 1}: M=5 angles')
        panel_idx += 1

    for ax in axes[:n_panels]:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel('Plane coord 1')
        ax.set_ylabel('Plane coord 2')

    for ax in axes[n_panels:]:
        ax.axis('off')

    plt.show()


plot_iters = target_iters
for it in plot_iters:
    trace_item = traces_by_iter.get(it)
    if trace_item is None:
        print(f'Skip iteration {it}: no trace available')
        continue
    plot_trace(trace_item, f'Iteration {it}')

    PLOT_FONT_SIZE = 18
SLICE_ALPHA = 0.7
SLICE_LINEWIDTH = 7.0
INTERVAL_COLOR = 'lightskyblue'
ELLIPSE_COLOR = 'black'
BRACKET_COLOR = 'tab:blue'
BRACKET_LEN_SCALE = 0.08
BRACKET_LINEWIDTH = 2.0
ALPHA_OFFSET = (14, -6)
LABEL_FONT_FAMILY = 'Helvetica'

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'Nimbus Roman', 'DejaVu Serif'],
    'font.sans-serif': ['Helvetica', 'Arial', 'Nimbus Sans', 'DejaVu Sans'],
    'font.monospace': ['Courier New', 'Courier', 'Nimbus Mono PS', 'DejaVu Sans Mono'],
    'mathtext.fontset': 'custom',
    'mathtext.rm': 'Times New Roman',
    'mathtext.it': 'Times New Roman:italic',
    'mathtext.bf': 'Times New Roman:bold',
    'mathtext.sf': 'Helvetica',
    'mathtext.tt': 'Courier New',
    'mathtext.default': 'rm',
})


def _half_arrow_label_pub(ax, x_end, y_end, text, offset=8, shift=(0.0, 0.0), fontsize=PLOT_FONT_SIZE):
    mid = np.array([0.5 * x_end, 0.5 * y_end], dtype=float)
    normal = np.array([-y_end, x_end], dtype=float)
    norm_len = np.linalg.norm(normal)
    if norm_len == 0:
        dx, dy = 0.0, 0.0
    else:
        normal /= norm_len
        dx, dy = normal * offset
    dx += shift[0]
    dy += shift[1]
    ax.annotate(text, xy=(mid[0], mid[1]), xytext=(dx, dy), textcoords='offset points', color='black', fontsize=fontsize)


def draw_base_ellipse_pub(ax, phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm, color=ELLIPSE_COLOR, aspect=1.0):
    xs, ys = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.plot(xs, ys, color=color, linewidth=1.2)
    ax.set_aspect(aspect, adjustable='box')
    return xs, ys


def annotate_angles_pub(
    ax,
    alpha_val,
    x_norm,
    nu_parallel,
    nu_perp_norm,
    nu_label_shift=(0.0, 0.0),
    nu_x_offset=0.0,
    fontsize=PLOT_FONT_SIZE,
 ):
    x0, y0 = ellipse_coords(alpha_val, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.annotate('$\\alpha$', xy=(x0, y0), xytext=ALPHA_OFFSET, textcoords='offset points', color='black', fontsize=fontsize)

    nu_phi = alpha_val + 0.5 * np.pi
    xnu, ynu = ellipse_coords(nu_phi, alpha_val, x_norm, nu_parallel, nu_perp_norm)

    ax.annotate('', xy=(x0, y0), xytext=(0.0, 0.0),
                arrowprops={'arrowstyle': '->', 'color': 'black', 'linewidth': 1.5})
    ax.annotate('', xy=(xnu, ynu), xytext=(0.0, 0.0),
                arrowprops={'arrowstyle': '->', 'color': 'black', 'linewidth': 1.5})
    _half_arrow_label_pub(ax, x0, y0, '$x$', offset=8, fontsize=fontsize)
    _half_arrow_label_pub(ax, xnu - nu_x_offset, ynu, '$\\nu$', offset=8, shift=nu_label_shift, fontsize=fontsize)

    xz, yz = ellipse_coords(0.0, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    dzx, dzy = _label_offset(xz, yz, base=12)


def plot_slice_segment_pub(ax, phi_grid, mask, alpha_val, x_norm, nu_parallel, nu_perp_norm, color='green', alpha=SLICE_ALPHA, linewidth=SLICE_LINEWIDTH):
    mask = np.asarray(mask, dtype=bool)
    if mask[0] and mask[-1]:
        phi_ext = np.concatenate([phi_grid, phi_grid[1:] + 2 * np.pi])
        mask_ext = np.concatenate([mask, mask[1:]])
        xs, ys = ellipse_coords(phi_ext, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        xs = xs.copy()
        ys = ys.copy()
        xs[~mask_ext] = np.nan
        ys[~mask_ext] = np.nan
        ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)
        return
    xs, ys = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    xs = xs.copy()
    ys = ys.copy()
    xs[~mask] = np.nan
    ys[~mask] = np.nan
    ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)


def draw_interval_arc_pub(ax, phi_min, phi_max, alpha_val, x_norm, nu_parallel, nu_perp_norm, color=INTERVAL_COLOR, linewidth=5.0, alpha=0.25):
    if phi_min <= phi_max:
        phi_arc = np.linspace(phi_min, phi_max, 200)
    else:
        phi_arc = np.concatenate([
            np.linspace(phi_min, 2 * np.pi, 150),
            np.linspace(0.0, phi_max, 150),
        ])
    xs, ys = ellipse_coords(phi_arc, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.plot(xs, ys, color=color, linewidth=linewidth, linestyle='-', alpha=alpha)


def _strip_axes(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)


def _plot_interval_panel(
    ax,
    trace_item,
    interval_index,
    pad=0.08,
    nu_label_shift=(0.0, 0.0),
    nu_x_offset=0.0,
    fontsize=PLOT_FONT_SIZE,
    aspect=1.0,
 ):
    x_centered = trace_item['x_centered']
    nu_centered = trace_item['nu_centered']
    alpha_val = trace_item['alpha']
    intervals = trace_item['intervals']
    accepted_phi = trace_item['accepted_phi']
    accepted_interval_idx = trace_item['accepted_interval_index']
    logy = trace_item['logy']

    u, w, x_norm, nu_parallel, nu_perp_norm = build_plane_basis(x_centered, nu_centered)
    phi_grid = np.linspace(0.0, 2 * np.pi, 600)

    ellipse_props = (
        problem.prior_mean()[:, np.newaxis]
        + np.cos(phi_grid - alpha_val) * x_centered[:, np.newaxis]
        + np.sin(phi_grid - alpha_val) * nu_centered[:, np.newaxis]
    )
    log_likes_grid = np.array([problem.log_likelihood(ellipse_props[:, i]) for i in range(phi_grid.size)])
    slice_mask = log_likes_grid > logy

    xs_all, ys_all = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    xlim = (xs_all.min() * (1 + pad), xs_all.max() * (1 + pad))
    ylim = (ys_all.min() * (1 + pad), ys_all.max() * (1 + pad))
    bracket_len = BRACKET_LEN_SCALE * max(xs_all.max() - xs_all.min(), ys_all.max() - ys_all.min())

    draw_base_ellipse_pub(ax, phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm, aspect=aspect)
    plot_slice_segment_pub(ax, phi_grid, slice_mask, alpha_val, x_norm, nu_parallel, nu_perp_norm)

    interval = intervals[interval_index]
    draw_interval_arc_pub(
        ax,
        interval['phi_min'],
        interval['phi_max'],
        alpha_val,
        x_norm,
        nu_parallel,
        nu_perp_norm,
    )
    draw_interval_brackets(
        ax,
        interval['phi_min'],
        interval['phi_max'],
        alpha_val,
        x_norm,
        nu_parallel,
        nu_perp_norm,
        bracket_len,
        color=BRACKET_COLOR,
        linewidth=BRACKET_LINEWIDTH,
        alpha=1.0,
    )
    plot_angle_markers(
        ax,
        interval['phi_vector'],
        alpha_val,
        x_norm,
        nu_parallel,
        nu_perp_norm,
        color='tab:red',
    )
    if interval_index == accepted_interval_idx:
        valid_indices = interval['valid_indices']
        if valid_indices.size > 0:
            plot_angle_markers(
                ax,
                interval['phi_vector'][valid_indices],
                alpha_val,
                x_norm,
                nu_parallel,
                nu_perp_norm,
                color='darkgreen',
            )
        xa, ya = ellipse_coords(accepted_phi, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        ax.scatter([xa], [ya], facecolors='none', edgecolors='black', s=150, marker='s', linewidths=1.0, clip_on=False, zorder=7)

    ax.scatter([0.0], [0.0], color='black', s=25, zorder=5)
    annotate_angles_pub(
        ax,
        alpha_val,
        x_norm,
        nu_parallel,
        nu_perp_norm,
        nu_label_shift=nu_label_shift,
        nu_x_offset=nu_x_offset,
        fontsize=fontsize,
    )
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.margins(0.04)
    _strip_axes(ax)


def plot_publication_row(traces, fontsize=PLOT_FONT_SIZE, wspace=0.08, third_shift=-0.02, save_dir=None):
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2))
    fig.subplots_adjust(wspace=wspace, left=0.03, right=0.97, bottom=0.12)
    panels = [
        (9998, 0, 0.2, (0.0, 0.0), 0.05, 2),
        (10011, 0, 0.08, (-6.0, 0.0), 0.0, 1.0),
        (10011, 1, 0.08, (-6.0, 0.0), 0.0, 1.0),
    ]
    panel_labels = ['(a)', '(b)', '(c)']

    for ax, (it, interval_index, pad, nu_label_shift, nu_x_offset, aspect), label in zip(axes, panels, panel_labels):
        trace_item = traces.get(it)
        if trace_item is None or interval_index >= len(trace_item['intervals']):
            ax.axis('off')
            continue
        _plot_interval_panel(
            ax,
            trace_item,
            interval_index,
            pad=pad,
            nu_label_shift=nu_label_shift,
            nu_x_offset=nu_x_offset,
            fontsize=fontsize,
            aspect=aspect,
        )
        ax.text(0.5, -0.08, label, transform=ax.transAxes, ha='center', va='top', fontsize=fontsize, fontfamily=LABEL_FONT_FAMILY)

    pos = axes[2].get_position()
    axes[2].set_position([pos.x0 + third_shift, pos.y0, pos.width, pos.height])

    from matplotlib.lines import Line2D
    from matplotlib.font_manager import FontProperties
    legend_handles = [
        Line2D([0], [0], color='green', linewidth=SLICE_LINEWIDTH, alpha=SLICE_ALPHA, label='Slice'),
        Line2D([0], [0], color=INTERVAL_COLOR, linewidth=2.5, label='Angle interval'),
        Line2D([0], [0], marker='o', color='tab:red', linestyle='None', markersize=6, label='Nonvalid proposals'),
        Line2D([0], [0], marker='o', color='darkgreen', linestyle='None', markersize=6, label='Valid proposals'),
        Line2D([0], [0], marker='s', markerfacecolor='none', markeredgecolor='black', linestyle='None', markersize=8, label='Accepted proposal'),
    ]
    legend_font = FontProperties(family=LABEL_FONT_FAMILY, size=fontsize)
    fig.legend(
        handles=legend_handles,
        loc='upper left',
        bbox_to_anchor=(0.03, 1.06),
        ncol=3,
        frameon=False,
        prop=legend_font,
    )

    if save_dir is not None:
        from pathlib import Path

        output_dir = Path(save_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'mess_ellipses_iters_9998_10011.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')

    plt.show()


plot_publication_row(
    traces_by_iter,
    wspace=-0.1,
    third_shift=-0.13,
    save_dir=''
 )