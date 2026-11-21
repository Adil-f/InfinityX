from app.services.classify import classify_query
from app.security import credit_cost


def test_routes_common_indicators():
    assert classify_query("35202-1234567-1")["query_type"] == "cnic"
    assert classify_query("3520212345671")["query_type"] == "ambiguous_numeric"
    assert classify_query("+393331234567")["query_type"] == "phone"
    assert classify_query("analyst@example.com")["query_type"] == "email"
    assert classify_query("8.8.8.8")["query_type"] == "ip"
    assert classify_query("example.com")["query_type"] == "domain"
    assert classify_query("https://example.com/path")["query_type"] == "url"
    assert classify_query("a" * 64)["query_type"] == "threat"
    assert classify_query("ada")["query_type"] == "username"
    assert classify_query("example.com", "username")["query_type"] == "username"


def test_local_modules_do_not_cost_a_credit():
    assert credit_cost("phone") == 0
    assert credit_cost("cnic") == 0
    assert credit_cost("forensics") == 0
    assert credit_cost("domain") == 1
    assert credit_cost("email") == 1
