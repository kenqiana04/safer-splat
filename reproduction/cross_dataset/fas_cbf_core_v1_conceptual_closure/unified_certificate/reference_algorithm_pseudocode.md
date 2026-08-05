# Reference algorithm pseudocode

Diagnose initial executability; apply recorded Start-Safe projection only when
certified; construct actuator-bounded current candidates; certify their interval;
require backup witness; then commit. Search alternatives only after nominal failure.
If a terminal action is certified, execute it. Otherwise fail closed. Re-certify
each period. Reference oracles cannot enter online decisions.
