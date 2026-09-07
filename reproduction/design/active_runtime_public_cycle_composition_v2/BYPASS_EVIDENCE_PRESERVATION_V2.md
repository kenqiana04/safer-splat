
# BYPASS evidence preservation V2

The implementation DAG is active-only. If it adds only an active composition
path, `Supervisor.bypass_decision`, `ActiveRunner.commit_bypass`, plant BYPASS
behavior, BYPASS trace, and canonical QA trace identity remain unchanged; PR
#119's frozen equivalence evidence is retained and regression-tested.

If a future implementation needs to change shared BYPASS semantics, it must
set `BYPASS_REVALIDATION_REQUIRED=true` and insert fresh BYPASS revalidation
after implementation and before active smoke. This design does not silently
reuse evidence under changed semantics.
