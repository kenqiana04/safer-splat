"""Read-only CBF coordinate/dimension contract audit."""
from pathlib import Path
import json
def main():
 out={'query_state_frame':'world metric coordinates x[..., :3]','gradient_frame_required':'world','hessian_frame_required':'world','f_position_frame':'world','g_acceleration_frame':'world','df_frame':'world','relative_degree':2,'hessian_per_gaussian_constraint':True,'active_min_hessian_used':False,'extension':'3x3 hessian is padded with 3x3 zero cross/velocity blocks to 6x6','required_products':['f.T @ H @ f','g.T @ H @ f'],'conclusion':'A local-frame hess_h is incompatible with current CBF products unless R is identity.'}
 root=Path(__file__).parent;(root/'cbf_hessian_downstream_contract.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');(root/'CBF_HESSIAN_FRAME_AND_DIMENSION_CONTRACT.md').write_text('# CBF Hessian frame and dimension contract\n\n`CBF.get_QP_matrices` passes world-frame state position to the Gaussian query, then uses `hes_h` in world-frame dynamics products. It pads the 3x3 spatial Hessian into a 6x6 relative-degree-two state Hessian. Hence the required frame is world, per Gaussian; no active-min Hessian is formed here. This audit executes no dynamics, CBF, or QP code.\n');print(json.dumps(out))
if __name__=='__main__':main()
