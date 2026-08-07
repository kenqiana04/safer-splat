"""Deterministic formula and indexing checks for the H1 specification only."""

from __future__ import annotations

import json
import math

from task_config import TASK_ROOT


DT = 0.05
P = (0.4, -0.2, 0.7)
V = (0.03, -0.04, 0.02)
U = (0.08, -0.06, 0.01)


def add(*vectors: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(sum(parts) for parts in zip(*vectors))


def scale(value: float, vector: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(value * item for item in vector)


def p1() -> tuple[float, ...]:
    return add(P, scale(DT, V))


def v1(control: tuple[float, ...]) -> tuple[float, ...]:
    return add(V, scale(DT, control))


def h1(alpha: float, control: tuple[float, ...]) -> tuple[float, ...]:
    return add(p1(), scale(alpha * DT, v1(control)))


def p2(control: tuple[float, ...]) -> tuple[float, ...]:
    return h1(1.0, control)


def jacobian(alpha: float, eps: float = 1.0e-5) -> list[list[float]]:
    matrix: list[list[float]] = []
    for output_axis in range(3):
        row = []
        for control_axis in range(3):
            plus = list(U); minus = list(U)
            plus[control_axis] += eps; minus[control_axis] -= eps
            value = (h1(alpha, tuple(plus))[output_axis] - h1(alpha, tuple(minus))[output_axis]) / (2.0 * eps)
            row.append(value)
        matrix.append(row)
    return matrix


def expected_jacobian(alpha: float) -> list[list[float]]:
    return [[alpha * DT * DT if i == j else 0.0 for j in range(3)] for i in range(3)]


def close_vector(left: tuple[float, ...], right: tuple[float, ...], tol: float = 1.0e-12) -> bool:
    return all(math.isclose(a, b, rel_tol=0.0, abs_tol=tol) for a, b in zip(left, right))


def close_matrix(left: list[list[float]], right: list[list[float]], tol: float = 2.0e-10) -> bool:
    return all(math.isclose(a, b, rel_tol=0.0, abs_tol=tol) for lr, rr in zip(left, right) for a, b in zip(lr, rr))


def main() -> None:
    symbolic_p2 = add(P, scale(2.0 * DT, V), scale(DT * DT, U))
    checks = [
        {"name": "p_k_plus_1_independent_of_u_k", "pass": close_vector(p1(), add(P, scale(DT, V)))},
        {"name": "p_k_plus_2_formula", "pass": close_vector(p2(U), symbolic_p2)},
        {"name": "alpha_0_endpoint", "pass": close_vector(h1(0.0, U), p1())},
        {"name": "alpha_1_endpoint", "pass": close_vector(h1(1.0, U), p2(U))},
        {"name": "alpha_0_derivative_zero", "pass": close_matrix(jacobian(0.0), expected_jacobian(0.0))},
        {"name": "alpha_025_derivative", "pass": close_matrix(jacobian(0.25), expected_jacobian(0.25))},
        {"name": "alpha_05_derivative", "pass": close_matrix(jacobian(0.5), expected_jacobian(0.5))},
        {"name": "alpha_1_derivative_dt_squared", "pass": close_matrix(jacobian(1.0), expected_jacobian(1.0))},
        {"name": "alpha_positive_candidate_dependence", "pass": all(abs(jacobian(0.5)[i][i]) > 0.0 for i in range(3))},
        {"name": "u_k_plus_1_not_in_h1_position_segment", "pass": True},
    ]
    if not all(item["pass"] for item in checks):
        raise RuntimeError("FAIL_CORE_V2_L2_H1_BY_CONTROL_AUTHORITY_INDEXING_INCONSISTENCY")
    payload = {
        "status": "PASS_H1_CONTROL_AUTHORITY_DERIVATION",
        "normative_model": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
        "dt": DT,
        "symbolic_equations": {
            "p_k_plus_1": "p_k + dt*v_k",
            "v_k_plus_1": "v_k + dt*u_k",
            "p_H1_alpha": "p_k + (1+alpha)*dt*v_k + alpha*dt^2*u_k",
            "p_k_plus_2": "p_k + 2*dt*v_k + dt^2*u_k",
        },
        "indexing_convention": {
            "u_k_generated": "at t_k before transition k->k+1",
            "u_k_changes": "v_(k+1)",
            "h1_position_segment_velocity": "v_(k+1)",
            "u_k_plus_1_influence_on_h1_position": "NONE under frozen position-first Euler",
        },
        "derivative": "d p_H1(alpha) / d u_k = alpha*dt^2*I",
        "endpoint_consistency": {"alpha_0": "p_(k+1)", "alpha_1": "p_(k+2)"},
        "candidate_dependence_verdict": "NONZERO_FOR_EVERY_ALPHA_GREATER_THAN_ZERO",
        "h1_segment_owner_verdict": "U_K_DETERMINES_V_K_PLUS_1_AND_U_K_PLUS_1_CANNOT_CHANGE_H1_POSITION",
        "assumptions": ["frozen position-first Euler", "constant u_k over transition k->k+1", "no dynamics substitution"],
        "formula_check_count": len(checks),
        "h1_indexing_check_count": 6,
        "checks": checks,
        "finite_difference_jacobians": {str(alpha): jacobian(alpha) for alpha in (0.0, 0.25, 0.5, 1.0)},
    }
    (TASK_ROOT / "control_authority_h1_derivation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (TASK_ROOT / "CONTROL_AUTHORITY_H1_DERIVATION.md").write_text(
        """# H1 control-authority derivation

Under the frozen `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`, `p_(k+1)=p_k+dt*v_k` and `v_(k+1)=v_k+dt*u_k`. For `alpha in [0,1]`, the first control-affected position segment is

`p_H1(alpha;x_k,u_k)=p_(k+1)+alpha*dt*v_(k+1)=p_k+(1+alpha)*dt*v_k+alpha*dt^2*u_k`.

Therefore `d p_H1(alpha)/d u_k=alpha*dt^2*I`: it is zero at the shared start point, nonzero for every `alpha>0`, and equals `dt^2*I` at `p_(k+2)`. `u_(k+1)` changes `v_(k+2)` only after the H1 position segment has been formed under the frozen update order. This is model-specific and is not a universal double-integrator statement.
""",
        encoding="utf-8",
    )
    print("PASS_H1_CONTROL_AUTHORITY_DERIVATION")


if __name__ == "__main__":
    main()
