from lakehouse_gov.exceptions import FinancialStatus as F
from lakehouse_gov.exceptions import JobsStatus as J
from lakehouse_gov.exceptions import classify_financial, classify_jobs


def test_absent_record_is_missing_not_zero():
    assert classify_financial(False, []) is F.MISSING
    assert classify_jobs(False, []) is J.MISSING


def test_reported_zero_is_a_submission():
    assert classify_financial(True, [0, 0, 0, 0]) is F.SUBMITTED
    assert classify_jobs(True, [0] * 6) is J.COMPLETE


def test_null_patterns():
    assert classify_financial(True, [None] * 4) is F.ALL_NULL
    assert classify_financial(True, [1, None, 1, 1]) is F.PARTIAL
    assert classify_jobs(True, [None] * 6) is J.ALL_NULL
    assert classify_jobs(True, [11, None, 4, None, None, None]) is J.PARTIAL


def test_exited_business_is_not_required():
    assert classify_financial(False, [], eligible=False) is F.NOT_REQUIRED
    assert classify_jobs(False, [], eligible=False) is J.NOT_REQUIRED
