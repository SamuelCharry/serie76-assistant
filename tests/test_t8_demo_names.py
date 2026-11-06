from unittest.mock import patch
from test_agent_scenarios import Base
from backend.auth.cli import ensure_demo_users
from backend.conversation.agent import run_agent


class DemoNamesTests(Base):
    def test_seeded_names_update_without_identity_or_password_change(self):
        with patch.dict('os.environ', {'DEMO_USERS_JSON': ''}):
            ensure_demo_users(self.connection)
            before = self.connection.execute("SELECT id,password_hash FROM series76.users WHERE email='demo@series76.test'").fetchone()
            self.connection.execute("UPDATE series76.users SET name='Test-only demo' WHERE email='demo@series76.test'")
            ensure_demo_users(self.connection)
            after = self.connection.execute("SELECT id,name,password_hash FROM series76.users WHERE email='demo@series76.test'").fetchone()
        self.assertEqual(after['name'], 'Demo Engineer')
        self.assertEqual(after['id'], before['id'])
        self.assertEqual(after['password_hash'], before['password_hash'])
        hello = run_agent(self.connection, 'Hello', [], {}, user_name=after['name'])
        self.assertTrue(hello.answer.startswith('Hello, Demo.'))
