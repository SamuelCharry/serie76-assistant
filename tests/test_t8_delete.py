from uuid import uuid4
from test_agent_scenarios import Base
from backend.conversation import store
from backend.auth.cli import create_user
from fastapi.testclient import TestClient
from scripts.agent_acceptance import scenario_environment
from backend.auth.api import require_user


class DeleteSessionTests(Base):
    def test_http_soft_delete_and_foreign_404(self):
        with scenario_environment() as (app, connection, owner):
            client = TestClient(app)
            created = client.post('/api/conversation', json={'query': 'Hello'}).json()
            session = created['session_id']
            app.dependency_overrides[require_user] = lambda: {'id': uuid4()}
            self.assertEqual(client.delete('/api/sessions/' + session).status_code, 404)
            app.dependency_overrides[require_user] = lambda: {'id': owner}
            self.assertEqual(client.delete('/api/sessions/' + session).status_code, 204)
            self.assertEqual(client.get('/api/sessions/' + session + '/messages').status_code, 404)
            self.assertEqual(client.post('/api/conversation', json={'session_id': session, 'query': 'Hello'}).status_code, 404)
            self.assertEqual(client.get('/api/sessions').json()['sessions'], [])

    def test_owner_isolation_and_hidden_history(self):
        owner = create_user(self.connection, 't8-owner@example.test', 'Owner', 'Owner-Passphrase-1')
        other = create_user(self.connection, 't8-other@example.test', 'Other', 'Other-Passphrase-2')
        session = uuid4()
        self.connection.execute('INSERT INTO series76.conversations(id,title,owner_id) VALUES (%s,%s,%s)',
                                (session, 'private', owner))
        with self.assertRaises(store.MissingSession):
            store.delete_session(self.connection, session, other)
        self.assertIsNotNone(store.get_session(self.connection, session, owner))
        store.delete_session(self.connection, session, owner)
        with self.assertRaises(store.MissingSession):
            store.get_session(self.connection, session, owner)
        self.assertEqual(store.list_sessions(self.connection, owner_id=owner), [])
        self.assertEqual(store.history(self.connection, session, owner_id=owner), [])
        with self.assertRaises(store.MissingSession):
            store.delete_session(self.connection, session, owner)
