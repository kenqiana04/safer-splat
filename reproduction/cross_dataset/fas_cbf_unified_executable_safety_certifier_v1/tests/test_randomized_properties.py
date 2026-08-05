from property_validation import run_property_validation


def test_frozen_randomized_properties():
    result=run_property_validation()
    assert result["randomized_segment_test_count"]==10_000
    assert result["randomized_backup_test_count"]==2_000
    assert result["randomized_fail_closed_test_count"]==1_000
    assert result["false_safe_count"]==0
    assert result["randomized_backup_success_count"]==2_000
    assert result["randomized_fail_closed_pass_count"]==1_000
