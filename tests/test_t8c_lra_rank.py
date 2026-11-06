"""LRA ranking uses SQL sourced current values and frequency scope."""
from backend.conversation import ranking
from backend.catalog.repository import get_actuator
from test_agent_scenarios import Base


class LraRankingTests(Base):
    def test_lra_measurement_and_ranking(self):
        a = get_actuator(self.connection, '763B00-11300000/A')
        b = get_actuator(self.connection, '763X30-11300000/A')
        self.assertEqual(ranking.measurement(a, 'lra', {'frequency_hz': 60}), 5)
        self.assertEqual(ranking.measurement(b, 'lra', {'frequency_hz': 60}), 2.9)
        self.assertEqual(ranking.rank([a, b], {'frequency_hz': 60}, 'lowest_lra')[0]['base_part_number'],
                         '763X30-11300000/A')
