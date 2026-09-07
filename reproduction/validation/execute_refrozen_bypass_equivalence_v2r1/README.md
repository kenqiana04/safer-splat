# Execute refrozen BYPASS equivalence V2R1

This directory freezes and executes the PR #118 V2R1 QA protocol. It asks only whether `ACTIVE_HARNESS_BYPASS` is bit-exactly transparent to the frozen Stonehenge reference control/plant path.

The real-arm order is `REF50, BYPASS50, REF10, BYPASS10, REF30, BYPASS30, REF70, BYPASS70, REF90, BYPASS90`. Every arm is a fresh process. The sentinel pair must pass before the remaining pairs. The real-arm cap is 10 and the post-start source-correction quota is zero.

This is noninterference QA only. ACTIVE mode, scientific oracle evaluation, official100, smoke, efficacy claims, and runtime-performance claims are outside scope.

