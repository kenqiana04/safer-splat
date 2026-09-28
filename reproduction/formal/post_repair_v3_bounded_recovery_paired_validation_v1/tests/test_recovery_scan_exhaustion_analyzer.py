from pathlib import Path
import json,sys
TASK=Path(__file__).resolve().parents[1]
FIXTURE=Path(__file__).resolve().parent/"fixtures/frozen_five_exhaustion_markers_v1.json"
sys.path.insert(0,str(TASK))
import analyze_post_repair_v3_bounded_recovery_paired_validation_v1 as analyzer
SCHEMA="EVALUATION_TRACE_SCHEMA_V2_CERT_EXEC_IDENTITY_V1"
ALLOWED="SOURCE_BOUNDED_LOCAL_RECOVERY_V1"
def context():
 return {"cycle_index":42,"routing_rule_ids":["REC_SCAN_EXHAUSTED","ARB_TERMINAL"],"phase_history":["RECOVERY_SOURCE_QUERY","ARBITRATION"]}
def marker():
 return {"exhaustion_key":"recovery-key:test","fallback_reason":"FALLBACK_TO_CERTIFIED_TERMINAL","final_disposition":"RECOVERY_SCAN_EXHAUSTED","plant_commit_authorized":False,"public_cycle_id":42,"recovery_scan_id":"recovery-scan:test","supervisor_selected":False}
def classify(record):
 return analyzer.classify_recovery_records([(record,context())],ALLOWED,SCHEMA)
def test_positive_exact_legitimate_exhaustion_is_not_a_blocker():
 result=classify(marker())
 assert result["legitimate_exhaustion_marker_count"]==1
 assert result["unauthorized_source_execution_count"]==0
 assert result["internal_recovery_loop_count"]==0
 assert result["invalid_internal_loop_action_bearing_count"]==0
def test_negative_selected_action_authority_stays_blocked():
 bad=marker(); bad["supervisor_selected"]=True
 result=classify(bad)
 assert result["legitimate_exhaustion_marker_count"]==0
 assert result["unauthorized_source_execution_count"]==1
 assert result["internal_recovery_loop_count"]>0
def test_negative_plantcommit_authority_stays_blocked():
 bad=marker(); bad["plant_commit_authorized"]=True
 result=classify(bad)
 assert result["legitimate_exhaustion_marker_count"]==0
 assert result["unauthorized_source_execution_count"]==1
 assert result["internal_recovery_loop_count"]>0
def test_negative_unauthorized_candidate_source_stays_blocked():
 bad=marker(); bad.update({"candidate_source":"SOURCE_UNAUTHORIZED_TEST","candidate_id":"candidate:test","candidate_rank":0,"canonical_action_identity":"control:test"})
 result=classify(bad)
 assert result["legitimate_exhaustion_marker_count"]==0
 assert result["unauthorized_source_execution_count"]==1
def test_negative_unknown_action_bearing_internal_event_stays_blocked():
 bad=marker(); bad.update({"final_disposition":"UNKNOWN_INTERNAL_RECOVERY_EVENT","candidate_source":ALLOWED,"action_role":"RECOVERY"})
 result=classify(bad)
 assert result["legitimate_exhaustion_marker_count"]==0
 assert result["unauthorized_source_execution_count"]==0
 assert result["invalid_internal_loop_action_bearing_count"]==1
 assert result["internal_recovery_loop_count"]==1
def test_all_five_frozen_real_records_match_exact_legitimate_schema():
 data=json.loads(FIXTURE.read_text(encoding="utf-8"))
 assert data["count"]==5
 assert data["source_sha256"]=="6722bc5b81b638ecf004221ef98bd995004601a5cecda105cef6f86da77cde5a"
 pairs=[(row["record"],row["cycle"]) for row in data["pairs"]]
 result=analyzer.classify_recovery_records(pairs,ALLOWED,SCHEMA)
 assert result["legitimate_exhaustion_marker_count"]==5
 assert result["unauthorized_source_execution_count"]==0
 assert result["same_key_duplicate_retry_count"]==0
 assert result["internal_recovery_loop_count"]==0
