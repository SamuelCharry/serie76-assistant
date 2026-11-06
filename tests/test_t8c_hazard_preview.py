"""Unconfirmed enclosure previews are identified as such to the reader."""
from test_agent_scenarios import Base


class HazardPreviewTests(Base):
    def test_refinery_preview_is_explicit(self):
        result = self.turn('for a refinery, 110 V',
                           ('search_actuators', {'supply_voltage_v': 110}))
        self.assertIn('Preview only: Explosionproof models', result.answer)
        self.assertNotIn('enclosure', result.context['filters'])
