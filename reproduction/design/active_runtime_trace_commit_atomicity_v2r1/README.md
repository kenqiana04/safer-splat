# Active Runtime Trace/Commit Atomicity V2R1 — design only

This directory freezes the smallest sufficient software consistency contract for PR #127's R-TRACE-001 blocker. The mechanical choice is **Option B: an in-memory software transaction state machine**. It retains confirmed execution facts across token/trace failures and moves incomplete or unresolved sessions out of `READY`; it does not claim physical ACID, process-crash durability, restart recovery, or filesystem durability.

The current engineering smoke may proceed with memory-only fail-close only after implementation validation, required BYPASS revalidation, complete post-trace reconformance, and separate smoke authorization. A durable journal is deferred until crash/restart recovery enters the formal runtime scope.
