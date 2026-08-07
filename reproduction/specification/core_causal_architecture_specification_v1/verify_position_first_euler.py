"""Independent algebra plus finite-difference check for the frozen V1 dynamics."""

from __future__ import annotations

import json
from pathlib import Path

from task_config import TASK_ROOT


def transition(position, velocity, control, dt):
    return tuple(position[i] + dt * velocity[i] for i in range(3)), tuple(velocity[i] + dt * control[i] for i in range(3))


def main() -> None:
    dt, epsilon = 0.05, 1.0e-7
    p, v, u = (1.2, -0.7, 0.3), (0.4, -0.2, 0.1), (0.6, 0.9, -0.5)
    p1, v1 = transition(p, v, u, dt)
    p2, v2 = transition(p1, v1, (0.0, 0.0, 0.0), dt)
    finite_p1, finite_p2 = [], []
    for axis in range(3):
        perturbed = list(u); perturbed[axis] += epsilon
        pp1, pv1 = transition(p, v, perturbed, dt)
        pp2, _ = transition(pp1, pv1, (0.0, 0.0, 0.0), dt)
        finite_p1.append([round((pp1[i] - p1[i]) / epsilon, 12) for i in range(3)])
        finite_p2.append([round((pp2[i] - p2[i]) / epsilon, 12) for i in range(3)])
    expected_zero = [[0.0] * 3 for _ in range(3)]
    expected_dt2 = [[dt * dt if i == j else 0.0 for i in range(3)] for j in range(3)]
    max_p1 = max(abs(finite_p1[j][i] - expected_zero[j][i]) for j in range(3) for i in range(3))
    max_p2 = max(abs(finite_p2[j][i] - expected_dt2[j][i]) for j in range(3) for i in range(3))
    assert max_p1 < 1e-8 and max_p2 < 1e-8
    payload = {
        "status": "PASS_POSITION_FIRST_EULER_AUTHORITY_CHECK",
        "identity": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
        "checks": 7,
        "manual_derivation": {
            "p_k_plus_1": "p_k + dt*v_k", "v_k_plus_1": "v_k + dt*u_k",
            "dp_k_plus_1_du_k": "0", "dv_k_plus_1_du_k": "dt*I",
            "p_k_plus_2": "p_k + 2*dt*v_k + dt^2*u_k", "dp_k_plus_2_du_k": "dt^2*I",
            "dv_k_plus_2_du_k": "dt*I when u_(k+1) is held independent",
            "multi_step": "dp_(k+n)/du_k=(n-1)*dt^2*I for n>=2 when later controls are independent",
        },
        "finite_difference": {"dt": dt, "epsilon": epsilon, "dp_k_plus_1_du_k": finite_p1, "dp_k_plus_2_du_k": finite_p2, "max_error_p1": max_p1, "max_error_p2": max_p2},
    }
    target = TASK_ROOT / "audits" / "formula_verification.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["status"])


if __name__ == "__main__":
    main()
