from certifier.result_types import Control,SegmentCertificate,SegmentStatus


def test_snapshot_change_invalidates_backup(moving_state,free_stack):
    original=free_stack["segment"].certify; calls={"n":0}
    def changing(state,control,expected):
        calls["n"]+=1
        if calls["n"]>=2:
            return SegmentCertificate(SegmentStatus.MAP_SNAPSHOT_MISMATCH,False,None,None,"TEST","EXACT_ANALYTIC","changed",0,"MAP_SNAPSHOT_MISMATCH")
        return original(state,control,expected)
    free_stack["segment"].certify=changing
    witness=free_stack["backup"].certify(moving_state,Control((0.,0.,0.),"NOMINAL","n"),"map-v1")
    assert not witness.certified and "MAP_SNAPSHOT_MISMATCH" in witness.reason_code
