"""Broad catalogue ranking acknowledges rows whose source says N/A."""
from test_agent_scenarios import Base


class NaScopeTests(Base):
    def test_unscoped_superlative_explains_excluded_na_rows(self):
        result = self.turn("what's the strongest?",
                           ('search_actuators', {'sort_by': ['highest_torque']}))
        self.assertIn('listed with N/A', result.answer)
        self.assertIn('64 actuators meet: the whole catalogue (no additional filters)', result.answer)
        self.assertIn('with published electrical data', result.answer)
