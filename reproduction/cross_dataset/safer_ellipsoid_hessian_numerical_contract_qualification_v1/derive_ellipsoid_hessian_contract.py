"""Write the KKT Hessian derivation used by the numerical reference."""
from pathlib import Path
def main():
 Path(__file__).with_name('ELLIPSOID_SIGNED_SQUARED_DISTANCE_HESSIAN_DERIVATION.md').write_text('''# Ellipsoid signed-squared-distance Hessian\n\nWith `F(lambda,u)=sum(a_i^2 u_i^2/(lambda+a_i^2)^2)-1=0`, KKT gives `y_i=a_i^2u_i/(lambda+a_i^2)`. Let `D_i=a_i^2/(lambda+a_i^2)`, `v_i=-a_i^2u_i/(lambda+a_i^2)^2`, `F_lambda=-2 sum(a_i^2u_i^2/(lambda+a_i^2)^3)`, and `F_u=2a_i^2u_i/(lambda+a_i^2)^2`. Then `d lambda/du=-F_u/F_lambda`, `J_y=diag(D)+v outer (d lambda/du)`, and on the regular fixed-sign domain `H_local=2 phi (I-J_y)`. For constant orthogonal `R`, `H_world=R H_local R^T`. Both are symmetric theoretically; active-min, sign-boundary, and nonunique projection cases are excluded from this second-order claim.\n''')
if __name__=='__main__':main()
