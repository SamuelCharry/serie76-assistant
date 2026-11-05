"""Changing an objective must replace the previous structured priority."""
from test_agent_scenarios import Base
from backend.conversation.agent import run_agent


class PriorityStateTests(Base):
    def seed(self):
        return self.turn('Find weatherproof 110 V on/off units; put larger torque first.',
            ('search_actuators', dict(enclosure='weatherproof',supply_voltage_v=110,
                                     service='on_off',priority=dict(metric='torque',direction='highest'))))

    def test_legacy_priority_replaces_structured_priority(self):
        first=self.seed()
        self.assertEqual(first.context['selection_priority']['metric'],'torque')
        result=self.turn('Now rank fastest.',('search_actuators',dict(refine=True,sort_by=['fastest'])))
        self.assertEqual(result.context['rank_by'],'fastest')
        self.assertNotIn('selection_priority',result.context)
        self.assertIn('fastest',result.recommendation['ranked_by'])

    def test_ui_priority_replaces_structured_priority(self):
        first=self.seed()
        result=run_agent(self.connection,'Rank by fastest',self.history,first.context,
                         action=dict(type='rank_by',args=dict(by='fastest')))
        self.assertEqual(result.context['rank_by'],'fastest')
        self.assertNotIn('selection_priority',result.context)
