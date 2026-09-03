"""Transaction-like PR #112 retained-backup token lifecycle."""

from __future__ import annotations

from dataclasses import replace

from .authority_registry import AuthorityRegistry
from .runtime_errors import TokenLifecycleViolation
from .runtime_types import (
    ActionRole,
    BundleIdentity,
    CertificateStatus,
    CommitReceipt,
    EvidenceResult,
    PreparedBackupBundle,
    RetainedBackupToken,
    RuntimeStateSnapshot,
    TokenIdentity,
    TokenLifecycle,
    canonical_sha256,
)


class BackupTokenStore:
    def __init__(self) -> None:
        self._active: RetainedBackupToken | None = None
        self._prepared: dict[str, PreparedBackupBundle] = {}

    @property
    def terminal_authorized(self) -> bool:
        return False

    def current(self) -> RetainedBackupToken | None:
        return self._active

    def prepare(self, bundle: PreparedBackupBundle) -> PreparedBackupBundle:
        if bundle.lifecycle != TokenLifecycle.PREPARED_UNCOMMITTED.value:
            raise TokenLifecycleViolation("ONLY_PREPARED_UNCOMMITTED_MAY_ENTER_STORE")
        self._prepared[bundle.identity.value] = bundle
        return bundle

    def validate(self, snapshot: RuntimeStateSnapshot, registry: AuthorityRegistry) -> EvidenceResult:
        token = self._active
        if token is None:
            return EvidenceResult(CertificateStatus.FAIL, "BACKUP_NONE", "none")
        checks = (
            token.lifecycle == TokenLifecycle.ACTIVE,
            token.expected_state_identity == snapshot.identity,
            token.expected_time_index == snapshot.cycle_index,
            token.bundle.map_identity == snapshot.map_identity == registry.map_identity,
            token.bundle.geometry_identity == registry.geometry.identity.value,
            token.bundle.actuator_identity == registry.actuator.identity.value,
            token.bundle.dynamics_identity == registry.dynamics.identity.value,
            token.current_action is not None,
            token.invalidation_reason is None,
        )
        if all(checks):
            return EvidenceResult(CertificateStatus.PASS, "BACKUP_TOKEN_STILL_VALID", token.identity.value)
        return EvidenceResult(CertificateStatus.FAIL, "BACKUP_TOKEN_INVALID", token.identity.value)

    def activate_after_navigation_commit(self, receipt: CommitReceipt, bundle_identity: BundleIdentity) -> RetainedBackupToken:
        bundle = self._prepared.get(bundle_identity.value)
        if bundle is None:
            raise TokenLifecycleViolation("PREPARED_BUNDLE_NOT_FOUND")
        if not receipt.committed or receipt.action_role not in {ActionRole.PRIMARY_NAVIGATION, ActionRole.ALTERNATIVE_NAVIGATION} or receipt.post_state is None:
            raise TokenLifecycleViolation("SOURCE_NAVIGATION_COMMIT_REQUIRED")
        material = {"bundle": bundle.identity, "activation_cycle": receipt.cycle_index + 1, "state": receipt.post_state.identity}
        new_token = RetainedBackupToken(
            TokenIdentity("token:sha256:" + canonical_sha256(material)),
            bundle,
            TokenLifecycle.ACTIVE,
            receipt.cycle_index + 1,
            0,
            receipt.post_state.identity,
            receipt.cycle_index + 1,
        )
        old = self._active
        self._active = new_token
        self._prepared.pop(bundle_identity.value)
        if old is not None and old.lifecycle == TokenLifecycle.ACTIVE:
            old = replace(old, lifecycle=TokenLifecycle.RETIRED_SUPERSEDED)
        return new_token

    def consume_after_backup_commit(self, receipt: CommitReceipt) -> RetainedBackupToken:
        token = self._active
        if token is None:
            raise TokenLifecycleViolation("NO_ACTIVE_BACKUP_TOKEN")
        if not receipt.committed:
            return token
        if receipt.action_role != ActionRole.RETAINED_BACKUP or receipt.post_state is None or token.current_action is None:
            raise TokenLifecycleViolation("VALID_BACKUP_COMMIT_REQUIRED")
        next_cursor = token.cursor + 1
        lifecycle = TokenLifecycle.EXHAUSTED if next_cursor >= len(token.bundle.tail_actions) else TokenLifecycle.ACTIVE
        updated = replace(
            token,
            lifecycle=lifecycle,
            cursor=next_cursor,
            expected_state_identity=receipt.post_state.identity,
            expected_time_index=receipt.cycle_index + 1,
        )
        self._active = updated
        return updated

    def abort_prepared(self, candidate_id: str) -> None:
        for key, bundle in tuple(self._prepared.items()):
            if bundle.source_candidate_identity.value == candidate_id:
                self._prepared.pop(key)

    def invalidate(self, reason: str) -> RetainedBackupToken | None:
        if self._active is None:
            return None
        self._active = replace(self._active, lifecycle=TokenLifecycle.INVALID, invalidation_reason=str(reason))
        return self._active
