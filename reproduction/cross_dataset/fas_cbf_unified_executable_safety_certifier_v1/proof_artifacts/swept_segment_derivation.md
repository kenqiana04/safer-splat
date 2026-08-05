# Swept-Segment Derivation

## Normative path

For `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`, the executed position
during one sample is `p(tau)=p_k+tau v_k`, `tau in [0,dt]`.  The current
acceleration changes velocity but not this immediate position segment.

## Exact isotropic primitive backend

For a represented sphere with center `c_j` and radius `r_j`, let
`d=p_1-p_0`.  The closest segment parameter is
`t_j=clip(((c_j-p_0)^T d)/(d^T d),0,1)`.  The exact signed primitive distance is
`s_j=||p_0+t_j d-c_j||-r_j`.  Taking `s_min=min_j s_j` and the monotone source
barrier transform `g(s)=sign(s)s^2` gives
`h_min=g(s_min)-r_effective^2-rho_seg`.  The implementation checks every
primitive directly for bounded maps or uses a cKDTree candidate set with a
proved midpoint-radius superset; no nearest possible primitive is omitted.

## Conservative general-Gaussian backend

For each closed Gaussian ellipsoid, signed Euclidean distance is 1-Lipschitz.
The pointwise minimum over ellipsoids remains 1-Lipschitz.  On an interval
`[a,b]` with midpoint `m`, every path point lies within
`0.5*(b-a)*||p_1-p_0||` of `p(m)`.  Therefore

```text
s(t) >= s(m) - 0.5*(b-a)*||p_1-p_0|| = s_lower.
```

Because `g(s)=sign(s)s^2` is monotone, a valid barrier lower bound is
`g(s_lower)-r_effective^2-rho_seg`.  An interval is certified only when this
lower bound is nonnegative. A finite negative exact query is an unsafe witness.
Otherwise the interval is subdivided, and budget exhaustion is reported as
`NOT_CERTIFIED_WITHIN_BUDGET`.

Dense sampling is diagnostic only. It can find counterexamples to an
implementation, but absence of a sampled counterexample never creates a formal
certificate.
