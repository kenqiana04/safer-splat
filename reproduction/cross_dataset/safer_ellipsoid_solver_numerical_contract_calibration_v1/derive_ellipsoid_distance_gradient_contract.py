"""Writes the mathematical derivation retained with this calibration."""
from pathlib import Path
def main():
 Path(__file__).with_name('ELLIPSOID_SIGNED_SQUARED_DISTANCE_GRADIENT_DERIVATION.md').write_text('''# Ellipsoid signed-squared-distance gradient\n\nFor fixed axes `a`, minimize `||x-y||^2` subject to `sum((y_i/a_i)^2)=1`. The KKT stationarity condition is `y-x + lambda diag(a^-2)y=0`, hence `y_i=a_i^2 x_i/(lambda+a_i^2)` and the scalar constraint is `sum(a_i^2 x_i^2/(lambda+a_i^2)^2)=1`. On the regular domain (unique projection, fixed inside/outside sign, no active-Gaussian tie), the envelope/Danskin derivative of the optimized value is `2(x-y*)`; for `h=phi d^2`, it is `2 phi (x-y*)`. This differentiates the value function, not the finite bisection program. Therefore reverse-mode through a finite branch graph may legitimately differ.\n''')
if __name__=='__main__':main()
