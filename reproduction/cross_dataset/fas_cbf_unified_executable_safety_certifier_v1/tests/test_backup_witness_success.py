from certifier.backup_witness import tail_witness_is_structurally_valid
from certifier.result_types import Control


def test_backup_witness_success(moving_state,free_stack):
    candidate=Control((0.,0.,0.),"NOMINAL","nominal")
    witness=free_stack["backup"].certify(moving_state,candidate,"map-v1")
    assert witness.certified and witness.terminal_certificate.certified
    assert witness.horizon==4
    assert all(s.certified for s in witness.per_segment_certificates)
    assert tail_witness_is_structurally_valid(witness)
