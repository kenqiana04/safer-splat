# CBF Hessian frame and dimension contract

`CBF.get_QP_matrices` passes world-frame state position to the Gaussian query, then uses `hes_h` in world-frame dynamics products. It pads the 3x3 spatial Hessian into a 6x6 relative-degree-two state Hessian. Hence the required frame is world, per Gaussian; no active-min Hessian is formed here. This audit executes no dynamics, CBF, or QP code.
