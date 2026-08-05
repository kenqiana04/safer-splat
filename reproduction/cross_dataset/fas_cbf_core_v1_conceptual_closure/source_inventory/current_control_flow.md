# Current control flow

Located baseline flow is nominal PD control, Gaussian CBF QP, position-first Euler
propagation, then barrier logging. V4-B adds one-step screening; V4-C evaluates
finite sequences; HCE stages search. These are not a single executable-safety
certifier. Current CBF source returns desired control after solver failure, while
run.py stops before propagation on a false solver flag; Core V1 resolves this with
one explicit non-execution contract.
