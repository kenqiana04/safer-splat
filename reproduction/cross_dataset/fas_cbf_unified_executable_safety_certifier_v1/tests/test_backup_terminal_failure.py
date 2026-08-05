from certifier.result_types import Control


def test_terminal_failure_invalidates_witness(moving_state,free_stack):
    original=free_stack["terminal"].certify
    def reject(*args,**kwargs):
        result=original(*args,**kwargs)
        return type(result)(False,result.terminal_state,False,result.assumptions,"FORCED_TERMINAL_FAILURE",result.velocity_tolerance,result.zero_hold_segment)
    free_stack["terminal"].certify=reject
    witness=free_stack["backup"].certify(moving_state,Control((0.,0.,0.),"NOMINAL","n"),"map-v1")
    assert not witness.certified and witness.reason_code.startswith("TERMINAL_CERTIFICATE_FAILED")
