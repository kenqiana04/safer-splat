# Alternative source requirements V2

The current controller establishes a baseline QP output as the primary proposal. `u_des` is merely a nominal reference. It does not establish a native finite sibling library.

The historical task-local `candidate_library.py` orders existing controls, task-local candidates, and a generated braking control, but it is not authority for the target active method. No synthetic, rotated, noisy, interpolated, perturbed, or outcome-fitted candidate is authorized here.

A future L4 contract must freeze pre-observation provenance, a finite bounded library, deterministic order, source legality, candidate identity, state/time alignment, and an outcome-independent generation policy. Every proposed alternative must pass full C0/L2/L3 recertification. Until that source contract is frozen, `ALT_AVAILABLE` is an abstract model branch and runtime L4 is blocked.
