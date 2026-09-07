
# Public cycle trace contract V2

Every resolved cycle has exactly one outcome trace with exact trial/cycle
identity. Navigation, backup, and terminal commits use the existing
ActiveRunner commit/trace path. A boundary uses the existing no-action trace
path. There is no trace-before-decision side effect, no untraced plant commit,
and no duplicate token update.

The coordinator records phase history, routing rule ids, deadline observations,
typed evidence references, final decision, commit receipt/boundary, and trace
reference. It never computes collision, progress, success, or oracle labels.
