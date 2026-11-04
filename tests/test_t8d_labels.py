"""Ranking reasons state the exact published scope used to order products."""
from backend.catalog.repository import get_actuator
from backend.conversation import ranking
from test_agent_scenarios import Base


class LabelTests(Base):
    def test_dc_and_unqualified_current_labels(self):
        dc = get_actuator(self.connection, '761X30-11370000/A')
        unqualified = get_actuator(self.connection, '761X30-11380000/A')
        self.assertIn('FLA (DC) 5 A', ranking.item(dc, {})['reason'])
        self.assertIn('FLA 5 A', ranking.item(unqualified, {})['reason'])

    def test_closest_qualifying_service_is_named(self):
        product = get_actuator(self.connection, '765B00-11300000/A')
        reason = ranking.item(product, {'min_torque_nm': 2500})['reason']
        self.assertIn('Modulating torque 2550 Nm (closest to 2500 Nm)', reason)

    def test_shared_torque_explains_service_once(self):
        product = get_actuator(self.connection, '764B00-11330C00/A')
        reason = ranking.item(product, {'service': 'on_off'})['reason']
        self.assertIn('same torque for On/Off and Modulating', reason)
