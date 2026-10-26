"""No real provider calls, secrets, or Streamlit cloud connectivity."""
import hashlib
import unittest

from ui.live_access import live_access_configured, verify_live_token

FLAG = "AGENT_LIVE_RESEARCH_ENABLED"
HASH = "AGENT_LIVE_ACCESS_SHA256"
TOKEN = "synthetic-only-owner-passcode-not-a-real-secret"
DIGEST = hashlib.sha256(TOKEN.encode()).hexdigest()


class LiveResearchGateTests(unittest.TestCase):
    def test_missing_config_defaults_to_demo_only(self):
        self.assertFalse(live_access_configured({}))
        self.assertFalse(verify_live_token(TOKEN, {}))

    def test_flag_only_fails_closed(self):
        self.assertFalse(live_access_configured({FLAG: "1"}))

    def test_hash_only_fails_closed(self):
        self.assertFalse(live_access_configured({HASH: DIGEST}))

    def test_non_exact_boolean_value_fails_closed(self):
        for flag in ["true", "True", "on", "0", "yes", " 01 "]:
            self.assertFalse(live_access_configured({FLAG: flag, HASH: DIGEST}), flag)

    def test_hash_must_be_valid_hex(self):
        for broken in ["x" * 64, "1", ""]:
            self.assertFalse(live_access_configured({FLAG: "1", HASH: broken}))

    def test_valid_config_requires_exact_private_token(self):
        env = {FLAG: "1", HASH: DIGEST}
        self.assertTrue(live_access_configured(env))
        self.assertTrue(verify_live_token(TOKEN, env))
        self.assertFalse(verify_live_token(TOKEN + "x", env))
        self.assertFalse(verify_live_token("", env))
        self.assertFalse(verify_live_token(None, env))

    def test_client_flags_cannot_enable_live_path(self):
        self.assertFalse(verify_live_token(TOKEN, {}))


if __name__ == "__main__":
    unittest.main()
