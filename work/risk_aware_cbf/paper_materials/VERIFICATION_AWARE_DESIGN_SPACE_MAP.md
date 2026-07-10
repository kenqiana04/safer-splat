# Verification-Aware Design Space Map

This map compares four families of verification-aware designs. It preserves
the distinction between a weak first implementation and a closed research
direction.

## Family A: Magnitude-Only Nominal Candidates

Representative version: VANS magnitude-only shadow v0.

Evidence:

- candidate set: N0 original, N1 scaled 0.75, N2 scaled 0.50;
- action semantics grounded for 3D acceleration-like commands;
- directional candidates unsupported;
- 1 verified opportunity over 189 warning steps;
- 0 progress-nonworse verified opportunities;
- C004 verified alternatives: 0;
- C006 verified alternatives: 0;
- runtime overhead about 5.3x for audit evaluation.

Interpretation:

- multi-candidate QP/verifier evaluation is feasible;
- magnitude-only candidate space is too weak for active promotion;
- this is a Level C current-mechanism failure, not closure of
  verification-aware selection.

## Family B: Controller-Compatible Directional / Action Primitives

Open questions:

- Current action semantics are 3D acceleration-like commands, not a grounded
  planar heading interface.
- Directional candidates cannot be introduced unless the action plane and
  physical meaning are audited.
- Legal primitives may be extractable from existing controller/dynamics only
  if they remain bounded and do not introduce waypoint generation.

Boundary risk:

- A rich directional primitive set can become a local planner.
- Any future version must start with a semantics audit and a fixed primitive
  list before active execution.

Current status:

- open, not selected as primary next prototype because unsupported action
  semantics are an immediate risk.

## Family C: Verification-Aware Supervisory Mode Selection

Mechanism:

- choose among existing bounded modes:
  - normal filtered command;
  - warning-gated slowdown;
  - triggered V4-C recovery;
  - safe halt.

Fit with SAFC:

- directly uses SAFC state/event coordination;
- avoids inventing new nominal action geometry;
- reuses V4-C positive evidence and slowdown diagnostic evidence;
- can be implemented as a small supervisor without planner integration.

Why it differs from failed versions:

- not scalar-only slowdown;
- not magnitude-only nominal candidate selection;
- not a new primitive MPC library;
- not selected-K candidate budgeting.

Current status:

- selected primary next redesign candidate.

## Family D: Verifier-Informed Nominal Objective Shaping

Mechanism options:

- add verifier-margin penalty;
- penalize deviation from nominal command;
- include compact progress proxy;
- select a bounded candidate that optimizes the shaped objective.

Risks:

- may modify CBF-QP or create nested optimization;
- may become a local planner if continuous action optimization is introduced;
- runtime may exceed V4-C without stronger benefit.

Current status:

- open as backup/future work;
- not primary because it has higher planner-boundary and runtime risk than
  supervisory mode selection.

## Family Comparison

| Family | Evidence status | Main benefit | Main weakness | Planner-boundary risk | Recommendation |
| --- | --- | --- | --- | --- | --- |
| A magnitude-only VANS | weak diagnostic | easy, grounded, no core changes | candidate space too small | low | freeze v0; keep lesson |
| B directional primitives | untested | may change direction without full planner | semantics not grounded | high | defer until semantics audit |
| C supervisory mode selection | untested but component-supported | reuses existing verified modes | mode choice may be conservative | medium-low | primary next prototype |
| D objective shaping | untested | can trade safety/progress before CBF | nested optimization risk | medium-high | backup/deferred |
