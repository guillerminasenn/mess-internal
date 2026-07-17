"""Phase scripts for AD dimension sweep with MESS/MH/pCN/mpCN."""


def run_phase1(*args, **kwargs):
	from .phase1_all import run

	return run(*args, **kwargs)


def run_phase2(*args, **kwargs):
	from .phase2_all import run

	return run(*args, **kwargs)



