# Design Figure Specifications

Every figure carries: **DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM**.

## 1. On-policy shadow dataflow

```mermaid
flowchart LR
  C["Frozen controller"] --> D["Decision commit: x_k, u_k"]
  D --> P["Frozen plant path"]
  D --> T["Immutable read-only tap"]
  T -->|"enqueue_nowait"| Q["Bounded queue"]
  Q --> W["Isolated L0/L1/L2 worker"]
  W --> L["Append-only log"]
```

## 2. Control-cycle observation timing

```mermaid
sequenceDiagram
  participant C as Frozen controller
  participant T as Read-only tap
  participant P as Plant
  participant W as Shadow worker
  C->>C: compute and accept u_k
  C->>T: immutable copy after commit
  T-->>W: nonblocking queue
  C->>P: apply same u_k
  W->>W: L0 then L1 then L2
```

## 3. Executed versus native candidate schema

```mermaid
flowchart TD
  G["Native candidate group"] --> E["Selected/executed: primary"]
  G --> N["Native non-executed: secondary"]
  G -. "never" .-> S["Synthetic candidate: prohibited"]
```

## 4. Prospective denominator funnel

```mermaid
flowchart TD
  A["All intended control steps"] --> B["Complete payloads plus explicit drops"]
  B --> C["L2 reached: selected"]
  C --> D["L2 evaluated"]
  D --> E["PASS"]
  D --> F["FAIL"]
  D --> U["UNKNOWN"]
```

## 5. Zero-authority boundary

```mermaid
flowchart LR
  A["Control authority zone"] --> B["One-way immutable payload"]
  B --> C["Observation-only zone"]
  C --> D["Evidence log"]
```

## 6. Frozen replay gaps to fixes

```mermaid
flowchart LR
  M["Missing u_k"] --> U["Mandatory post-commit u_k"]
  R["Unknown reachability"] --> X["Explicit runtime stage reasons"]
  I["Map path only"] --> H["Content-addressed map manifest"]
  C["Mixed candidate roles"] --> T["Executed primary / native secondary"]
```

## 7. Future phase gates

```mermaid
flowchart LR
  P0["Phase 0: implementation QA"] --> G0["Static/schema gates"]
  G0 --> P1["Phase 1: equivalence"]
  P1 --> G1["Control-trace gate"]
  G1 --> P2["Phase 2: logging pilot"]
  P2 --> G2["Completeness gate"]
  G2 --> P3["Phase 3: frozen cohort"]
  P3 --> P4["Phase 4: analysis only"]
```
