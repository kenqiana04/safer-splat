# Downstream query contract audit

`CBF.get_QP_matrices` consumes `h`, `grad_h`, and `hes_h`; the Hessian enters both second-order Lie-derivative terms. The calibrated contract therefore covers only query/state gradient, not the required Hessian. No downstream execution occurred.
