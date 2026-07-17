"""Experiment workflows for AD dimension sweep with MESS/MH/pCN/mpCN."""


def run_workflow(*args, **kwargs):
	from .run_workflow import run

	return run(*args, **kwargs)


def compute_metrics_workflow(*args, **kwargs):
	from .compute_metrics_workflow import run

	return run(*args, **kwargs)


def report_workflow(*args, **kwargs):
	from .report_workflow import run

	return run(*args, **kwargs)


def run_phase1(*args, **kwargs):
	from .phase1_all import run

	return run(*args, **kwargs)


def run_phase2(*args, **kwargs):
	from .phase2_all import run

	return run(*args, **kwargs)



