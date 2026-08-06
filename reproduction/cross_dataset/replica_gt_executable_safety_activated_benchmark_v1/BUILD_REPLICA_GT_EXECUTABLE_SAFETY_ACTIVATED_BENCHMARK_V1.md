# BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1

This task evaluates the PR #84 certifier on one frozen Replica GT-derived Gaussian map only if the nested B0–B3 method matrix is executable from fully frozen inputs. The scientific unit is a state or episode, not a step. Reference geometry is forbidden before registry lock and never enters online certification.

The first hard gate is method fairness. In particular, B3 requires an upstream-frozen alternative-control value set, size, IDs, provenance, ordering, and canonical identity. A sorting function or caller-supplied tuple alone is not a frozen candidate library. Missing content triggers `BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH`; no task-local alternative set may be invented.

No map training or mutation, dataset switch, parameter tuning, large-scale navigation, learned-map deployment, real-time claim, mathematical-unrecoverability claim, or global FAS-CBF superiority claim is authorized.
