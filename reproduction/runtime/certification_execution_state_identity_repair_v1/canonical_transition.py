"""Pure execution-equivalent transition arithmetic and bitwise identities."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import struct
from typing import Any, Callable, Iterable

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import canonical_sha256


CANONICAL_DTYPE = "IEEE754_BINARY32_TORCH_FLOAT32"
CANONICAL_OP_ORDER = "x + double_integrator_dynamics(x,u) * float(dt)"
CANONICAL_SERIALIZATION = "detach.cpu.tolist.then_python_float_tuple"
NEUTRAL_ACTION = (0.0, 0.0, 0.0)


def _tuple(values: Iterable[Any], size: int) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != size:
        raise ValueError(f"CANONICAL_VECTOR_SIZE_REQUIRED:{size}")
    return result


def binary32_hex(values: Iterable[Any]) -> tuple[str, ...]:
    """Return the exact IEEE-754 binary32 bit pattern of scalar values."""

    return tuple(struct.pack(">f", float(value)).hex() for value in values)


@dataclass(frozen=True)
class CanonicalTransitionIdentity:
    value: str
    dtype: str
    device_backend: str
    operation_order: str
    dynamics_identity: str
    serialization: str


@dataclass(frozen=True)
class CanonicalTransitionResult:
    pre_state: tuple[float, ...]
    action: tuple[float, ...]
    dt: float
    post_state: tuple[float, ...]
    pre_state_identity: str
    action_identity: str
    post_state_identity: str
    transition_identity: str


class CanonicalExecutionTransition:
    """Side-effect-free transition matching the frozen plant numerical graph."""

    def __init__(
        self,
        device: Any = "cpu",
        *,
        dynamics: Callable[[Any, Any], Any] | None = None,
        backend_label: str | None = None,
    ) -> None:
        torch = importlib.import_module("torch")
        self._torch = torch
        self.device = torch.device(device)
        self._dynamics = dynamics or importlib.import_module("dynamics.systems").double_integrator_dynamics
        if backend_label is None:
            if self.device.type == "cuda":
                index = self.device.index if self.device.index is not None else torch.cuda.current_device()
                backend_label = f"torch:{torch.__version__}:cuda:{index}:{torch.cuda.get_device_name(index)}"
            else:
                backend_label = f"torch:{torch.__version__}:cpu"
        material = {
            "schema": "CANONICAL_EXECUTION_TRANSITION_IDENTITY_V1",
            "dtype": CANONICAL_DTYPE,
            "device_backend": str(backend_label),
            "operation_order": CANONICAL_OP_ORDER,
            "dynamics_identity": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
            "serialization": CANONICAL_SERIALIZATION,
        }
        self.identity = CanonicalTransitionIdentity(
            "canonical-transition:sha256:" + canonical_sha256(material),
            CANONICAL_DTYPE,
            str(backend_label),
            CANONICAL_OP_ORDER,
            material["dynamics_identity"],
            CANONICAL_SERIALIZATION,
        )

    @staticmethod
    def vector_identity(kind: str, values: Iterable[Any]) -> str:
        bits = binary32_hex(values)
        return f"canonical-{kind}:sha256:" + canonical_sha256({"kind": kind, "binary32_hex": bits})

    def state_identity(self, state: Iterable[Any]) -> str:
        return self.vector_identity("state", _tuple(state, 6))

    def position_identity(self, position: Iterable[Any]) -> str:
        return self.vector_identity("position", _tuple(position, 3))

    def action_identity(self, action: Iterable[Any]) -> str:
        return self.vector_identity("action", _tuple(action, 3))

    @staticmethod
    def bitwise_equal(left: Iterable[Any], right: Iterable[Any]) -> bool:
        return binary32_hex(left) == binary32_hex(right)

    def evaluate(self, state: Iterable[Any], action: Iterable[Any], dt: float) -> CanonicalTransitionResult:
        state_v = _tuple(state, 6)
        action_v = _tuple(action, 3)
        x = self._torch.tensor(state_v, device=self.device, dtype=self._torch.float32)
        u = self._torch.tensor(action_v, device=self.device, dtype=self._torch.float32)
        post_tensor = x + self._dynamics(x, u) * float(dt)
        post = tuple(float(value) for value in post_tensor.detach().cpu().tolist())
        return CanonicalTransitionResult(
            state_v,
            action_v,
            float(dt),
            post,
            self.state_identity(state_v),
            self.action_identity(action_v),
            self.state_identity(post),
            self.identity.value,
        )

    def transition(self, state: Iterable[Any], action: Iterable[Any], dt: float) -> tuple[float, ...]:
        return self.evaluate(state, action, dt).post_state

    def immediate_position(self, state: Iterable[Any], dt: float) -> tuple[float, float, float]:
        return self.transition(state, NEUTRAL_ACTION, dt)[:3]  # type: ignore[return-value]

    def two_step(
        self,
        state: Iterable[Any],
        action_k: Iterable[Any],
        dt: float,
        action_k1: Iterable[Any] = NEUTRAL_ACTION,
    ) -> tuple[CanonicalTransitionResult, CanonicalTransitionResult]:
        first = self.evaluate(state, action_k, dt)
        second = self.evaluate(first.post_state, action_k1, dt)
        return first, second

    def segment_identity(self, start: Iterable[Any], end: Iterable[Any], map_identity: str, radius: float, rho: float) -> str:
        material = {
            "start_binary32": binary32_hex(_tuple(start, 3)),
            "end_binary32": binary32_hex(_tuple(end, 3)),
            "map_identity": str(map_identity),
            "effective_radius": float(radius),
            "rho_seg": float(rho),
            "transition_identity": self.identity.value,
            "closed": True,
        }
        return "canonical-segment:sha256:" + canonical_sha256(material)
