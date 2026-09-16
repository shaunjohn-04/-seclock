
from fastapi.testclient import TestClient
from main import app, state

client = TestClient(app)


# ---------------------------------------------------------------------------
# Synthetic test fixtures
# These values are intentionally fake and should only be used for testing.
# ---------------------------------------------------------------------------

TEST_OWNER_NAME = "Test Owner"
TEST_OWNER_PHONE = "+91 90000 00000"
TEST_OWNER_EMAIL = "test.owner@example.com"

TEST_NOMINEES = [
    {
        "name": "Test Nominee One",
        "phone": "+91 90000 00001",
        "relation": "Daughter",
    },
    {
        "name": "Test Nominee Two",
        "phone": "+91 90000 00002",
        "relation": "Son",
    },
    {
        "name": "Test Nominee Three",
        "phone": "+91 90000 00003",
        "relation": "Sister",
    },
    {
        "name": "Test Nominee Four",
        "phone": "+91 90000 00004",
        "relation": "Legal Counsel",
    },
    {
        "name": "Test Nominee Five",
        "phone": "+91 90000 00005",
        "relation": "Spouse",
    },
]

TEST_BANK = "Test Bank"
TEST_ACCOUNT = "TEST-ACCOUNT-001"
TEST_BALANCE = "TEST-BALANCE"

TEST_EMAIL_CREDENTIAL = "test.credentials@example.com"


def test_e2e():
    print("==========================================================================")
    print(" Running End-to-End Automated Integration Tests for Seclock ")
    print("==========================================================================")

    # 1. Initial system state

    state.reset()

    res = client.get("/api/state")

    assert res.status_code == 200
    assert res.json()["is_vault_setup"] is False

    print("✓ Initial system state test PASSED")

    # 2. Vault Setup & Shamir 3-of-5 Key Splitting

    setup_payload = {
        "owner_name": TEST_OWNER_NAME,
        "owner_phone": TEST_OWNER_PHONE,
        "owner_email": TEST_OWNER_EMAIL,
        "preferred_channels": ["App", "SMS", "IVR"],
        "check_in_interval_days": 30,
        "nominees": TEST_NOMINEES,
        "tier1_assets": [
            {
                "bank": TEST_BANK,
                "acc": TEST_ACCOUNT,
                "balance": TEST_BALANCE,
            }
        ],
        "tier2_assets": [
            {
                "credentials": TEST_EMAIL_CREDENTIAL,
            }
        ],
        "tier3_assets": [
            {
                "note": "Synthetic test asset details",
            }
        ],
    }

    res = client.post(
        "/api/vault/setup",
        json=setup_payload,
    )

    assert res.status_code == 200

    data = res.json()

    assert data["status"] == "SUCCESS"
    assert len(data["shares"]) == 5

    shares = data["shares"]

    print(
        f"✓ Vault Setup PASSED "
        f"(Generated 5 shares with threshold {state.threshold_k})"
    )

    # 3. Multi-Channel Liveness Check-ins

    res = client.post(
        "/api/liveness/check-in",
        json={
            "channel": "App",
            "response_code": "TEST_APP_BIOMETRIC",
        },
    )

    assert res.status_code == 200
    assert res.json()["liveness_status"] == "ACTIVE"

    res = client.post(
        "/api/liveness/check-in",
        json={
            "channel": "SMS",
            "response_code": "TEST_SMS_CODE",
        },
    )

    assert res.status_code == 200

    res = client.post(
        "/api/liveness/check-in",
        json={
            "channel": "IVR",
            "response_code": "TEST_IVR_CODE",
        },
    )

    assert res.status_code == 200

    print(
        "✓ Multi-Channel Check-in "
        "(App, SMS, IVR) test PASSED"
    )

    # 4. Liveness Miss Simulation

    res = client.post(
        "/api/liveness/simulate-miss",
    )

    assert res.status_code == 200
    assert res.json()["status"] == "EXPIRED"

    print(
        "✓ Liveness Escalation & Expiry simulation PASSED"
    )

    # 4b. Life Certificate Upload & Liveness Restoration

    life_cert_text = """
    SYNTHETIC TEST DOCUMENT
    DIGITAL LIFE CERTIFICATE
    Pramaan ID: TEST-LIFE-CERT-001
    Account Owner / Pensioner: TEST OWNER
    Biometric Verification: TEST_VERIFIED
    Issuing Authority: TEST AUTHORITY
    Status: ACTIVE — TEST PERSON CONFIRMED ALIVE
    """

    res = client.post(
        "/api/liveness/upload-life-certificate",
        json={
            "document_text": life_cert_text,
        },
    )

    assert res.status_code == 200

    life_res = res.json()

    assert life_res["status"] == "VERIFIED_ALIVE"

    assert (
        client.get("/api/state").json()["liveness_status"]
        == "ACTIVE"
    )

    print(
        "✓ Life Certificate Upload & "
        "Liveness Restoration PASSED"
    )

    # Re-expire for claim testing

    client.post(
        "/api/liveness/simulate-miss",
    )

    # 5. Legal Document OCR Verification

    doc_text = """
    SYNTHETIC TEST DOCUMENT
    TEST DEPARTMENT
    TEST FORM — DEATH CERTIFICATE
    Registration Number: TEST-DEATH-CERT-001
    Date of Death: 01/01/2025
    Name of Deceased: TEST OWNER
    Nominee / Informant Name: TEST NOMINEE ONE
    Issuing Authority: TEST AUTHORITY
    """

    res = client.post(
        "/api/ocr/verify-document",
        json={
            "document_text": doc_text,
        },
    )

    assert res.status_code == 200

    ocr_res = res.json()

    assert ocr_res["status"] == "VERIFIED"
    assert ocr_res["confidence_score"] >= 70

    print(
        f"✓ Synthetic Legal Document OCR Verification PASSED "
        f"(Confidence: {ocr_res['confidence_score']}%)"
    )

    # 6. Submit Nominee Shares
    # 2 shares -> Pending
    # 3 shares -> Reconstructed

    # Share 1

    s1 = shares[0]

    res = client.post(
        "/api/claim/submit-share",
        json={
            "nominee_name": "Test Nominee One",
            "share_index": s1["share_index"],
            "share_hex": s1["share_hex"],
        },
    )

    assert res.status_code == 200
    assert res.json()["is_reconstructed"] is False

    # Share 2

    s2 = shares[1]

    res = client.post(
        "/api/claim/submit-share",
        json={
            "nominee_name": "Test Nominee Two",
            "share_index": s2["share_index"],
            "share_hex": s2["share_hex"],
        },
    )

    assert res.status_code == 200
    assert res.json()["is_reconstructed"] is False

    print(
        "✓ Partial nominee shares "
        "(2/5) correctly held pending threshold"
    )

    # Share 3 - Meets 3-of-5 threshold

    s3 = shares[2]

    res = client.post(
        "/api/claim/submit-share",
        json={
            "nominee_name": "Test Nominee Three",
            "share_index": s3["share_index"],
            "share_hex": s3["share_hex"],
        },
    )

    assert res.status_code == 200

    claim_res = res.json()

    assert claim_res["is_reconstructed"] is True
    assert claim_res["decrypted_vault"] is not None

    assert (
        claim_res["decrypted_vault"]["tier1_financial"][0]["bank"]
        == TEST_BANK
    )

    print(
        "✓ Threshold Master Key Reconstruction & "
        "Decryption PASSED (3-of-5 shares)"
    )

    # 7. Audit Ledger Integrity

    res = client.get(
        "/api/audit/ledger",
    )

    assert res.status_code == 200

    ledger_res = res.json()

    assert ledger_res["integrity"]["is_valid"] is True

    print(
        f"✓ Tamper-Evident SHA-256 Audit Ledger PASSED "
        f"({ledger_res['compliance_report']['total_audit_events']} "
        f"blocks verified)"
    )

    # 8. Tamper Detection

    res = client.post(
        "/api/audit/simulate-tamper?block_index=1",
    )

    assert res.status_code == 200

    assert (
        res.json()["new_integrity"]["is_valid"]
        is False
    )

    print(
        "✓ Cryptographic Tampering Detection PASSED"
    )

    # 9. Emergency Owner Veto

    res = client.post(
        "/api/owner/veto",
    )

    assert res.status_code == 200

    assert (
        res.json()["status"]
        == "VETO_EXECUTED"
    )

    print(
        "✓ Emergency Account Owner Veto PASSED"
    )

    print("==========================================================================")
    print(" ALL 9 SECLOCK E2E VERIFICATION TESTS PASSED SUCCESSFULLY! ")
    print("==========================================================================")
```

Save it, then run:

```bash
cd ~/seclock
python3 -m pytest test_e2e.py -v
```

If it passes, commit and push:

```bash
git add test_e2e.py
git commit -m "Use synthetic fixtures in E2E tests"
git push origin main
```

Then trigger the Jenkins build.

