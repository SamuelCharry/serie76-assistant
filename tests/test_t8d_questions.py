"""A question is useful only if its options reduce the actual candidate set."""
from backend.conversation import interactions
from test_agent_scenarios import Base


class QuestionTests(Base):
    def test_service_full_overlap_is_suppressed(self):
        code_set = ['A', 'B', 'C']
        facets = {'service': [dict(value='on_off', n=3, codes=code_set),
                              dict(value='modulating', n=3, codes=code_set)]}
        self.assertEqual(interactions.questions(facets, ['service']), [])

    def test_knm_three_phase_does_not_ask_full_overlap_service(self):
        result = self.turn('min torque 1.2kNm, 3 fases', ('search_actuators', {}))
        self.assertNotIn('service', [q['id'] for q in (result.interaction or {}).get('questions', [])])
