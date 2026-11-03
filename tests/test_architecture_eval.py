"""Offline contracts and budget tests: no paid API calls."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import os

from architecture_eval.cases import SCENARIOS, PILOT_IDS
from architecture_eval.context import extract_chunks
from architecture_eval.engine import explain, Workflow, TOOLS
from architecture_eval.provider import Budget, BudgetStop, PaidRouter
from architecture_eval.scoring import score_turn
from backend.conversation.agent import AgentResult, AgentUnavailable
from model_eval.google import API_ROOT, ProviderFailure

CONFIG = json.loads(Path("config/architecture_eval.json").read_text())


class BudgetTests(unittest.TestCase):
    def test_reservation_survives_failed_request_and_restart(self):
        with TemporaryDirectory() as folder:
            budget = Budget(folder, dict(CONFIG, min_interval_seconds=0))
            with patch("architecture_eval.provider.request_json", side_effect=ProviderFailure(503, "upstream_error")):
                with self.assertRaises(ProviderFailure):
                    budget.request(API_ROOT+"models/fixture:generateContent", "synthetic", {})
            self.assertGreater(Budget(folder, CONFIG).spent(), 0)
            events = budget.events()
            self.assertEqual(events[-1]["charged_usd"], events[0]["reserved_usd"])

    def test_cap_blocks_before_network(self):
        with TemporaryDirectory() as folder:
            budget = Budget(folder, dict(CONFIG, budget_usd=0.00001))
            with patch("architecture_eval.provider.request_json") as request:
                with self.assertRaises(BudgetStop):
                    budget.request(API_ROOT+"models/fixture:generateContent", "synthetic", {})
                request.assert_not_called()
            self.assertTrue(budget.blocked)

    def test_thinking_tokens_are_charged(self):
        with TemporaryDirectory() as folder:
            budget = Budget(folder, CONFIG)
            with patch("architecture_eval.provider.request_json", return_value={"usageMetadata":{"promptTokenCount":100,"candidatesTokenCount":10,"thoughtsTokenCount":20}}):
                budget.request(API_ROOT+"models/fixture:generateContent", "synthetic", {})
            self.assertAlmostEqual(budget.spent(), (100*.75+30*3.75)/1e6)

    def test_unknown_usage_keeps_reservation(self):
        with TemporaryDirectory() as folder:
            budget = Budget(folder, CONFIG)
            with patch("architecture_eval.provider.request_json", return_value={}):
                budget.request(API_ROOT+"models/fixture:embedContent", "synthetic", {})
            self.assertEqual(budget.events()[0]["charged_usd"], budget.spent())


class CorpusTests(unittest.TestCase):
    def test_budget_stop_is_not_model_quality_failure(self):
        from scripts.analyze_architecture_eval import quality_failure
        row=dict(failure={"provider_failure":False},budget_stopped=True)
        self.assertFalse(quality_failure(row))
        row["budget_stopped"]=False
        self.assertTrue(quality_failure(row))

    def test_resume_normalizes_json_tuples_but_rejects_config_change(self):
        from architecture_eval import __main__ as experiment
        from scripts.continue_architecture_eval import json_asdict
        with TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"index.json").write_text('{}')
            with patch.object(experiment,"ROOT",root):
                experiment.freeze(CONFIG)
                with patch.object(experiment,"asdict",json_asdict):
                    experiment.freeze(CONFIG)
                    with self.assertRaises(ValueError):
                        experiment.freeze(dict(CONFIG,budget_usd=.51))

    def test_paired_analysis_counts_schema_failure_as_quality(self):
        from scripts.analyze_architecture_eval import paired_ids
        rows=[dict(scenario="s",configuration="A",budget_stopped=False,failure=None),
              dict(scenario="s",configuration="B",budget_stopped=False,failure={"provider_failure":False})]
        self.assertEqual(paired_ids(rows,["A","B"]),{"s"})
        rows[1]["failure"]["provider_failure"]=True
        self.assertEqual(paired_ids(rows,["A","B"]),set())

    def test_balanced_unique_corpus_and_pilot(self):
        self.assertEqual(len(SCENARIOS), 24)
        self.assertEqual(len({s.id for s in SCENARIOS}),24)
        self.assertEqual({sum(s.category==c for s in SCENARIOS) for c in {s.category for s in SCENARIOS}}, {4})
        self.assertTrue(set(PILOT_IDS).issubset({s.id for s in SCENARIOS}))
        self.assertEqual(len({t.name for t in TOOLS}),4)

    def test_chunks_bound_pages_and_token_limits(self):
        chunks = extract_chunks("data/raw/series_76_summary.pdf")
        self.assertEqual({c["page"] for c in chunks},{1,2})
        self.assertTrue(all(c["token_count"]<=300 for c in chunks))
        self.assertTrue(all(c["document"]=="series_76_summary.pdf" for c in chunks))

    def test_unknown_fragment_is_rejected(self):
        with self.assertRaises(ValueError):
            explain({"fragment_ids":["invented"]},[],{})

    def test_context_never_promotes_summary_numbers(self):
        fragments=[dict(id="x",page=1,document="series_76_summary.pdf",text="Motor rating is 999 W. It describes the internal motor.")]
        result=explain({"fragment_ids":["x"]},fragments,{})
        self.assertNotIn("999",result.answer)
        self.assertIn("internal motor",result.answer)
        self.assertEqual(result.products,[])

    def test_added_filter_is_not_a_success(self):
        turn=next(s for s in SCENARIOS if s.id=="trap_shared").turns[0]
        result=AgentResult("",[],[dict(name="search_actuators",parameters=dict(turn.args,frequency_hz=60),data={"total":7})])
        scored=score_turn(turn,result,[])
        self.assertFalse(scored["passed"])
        self.assertTrue(scored["unrequested_or_changed_filters"])

    def test_context_keywords_without_provenance_fail(self):
        turn=next(s for s in SCENARIOS if s.id=="context_fla").turns[0]
        result=AgentResult("load current",[],[dict(name="explain_context",parameters={},data={})])
        self.assertFalse(score_turn(turn,result,[])["passed"])


class ScriptedChat:
    def __init__(self, call):
        self.call, self.metadata = call, {"fixture":True}

    def bind_tools(self, *args, **kwargs):
        return self

    def invoke(self, *args, **kwargs):
        return SimpleNamespace(tool_calls=[dict(name=self.call[0],args=self.call[1])])


class FakeStore:
    def __init__(self):
        self.calls = 0

    def search(self, query):
        self.calls += 1
        return [dict(id="x",page=2,document="series_76_summary.pdf",text="Motor Power describes the internal motor.",distance=.1)]


@unittest.skipUnless(os.environ.get("ARCH_EVAL_TEST_DB")=="1", "Requires isolated experimental PostgreSQL")
class WorkflowDatabaseTests(unittest.TestCase):
    def workflow(self, sequence):
        from architecture_eval.__main__ import connection
        conn=connection()
        self.addCleanup(conn.close)
        calls=iter(sequence)
        store=FakeStore()
        return Workflow(conn,store,lambda:ScriptedChat(next(calls))),store

    def test_five_topologies_real_sql(self):
        get=("get_actuator",{"part_numbers":["761A00-11300000/A"],"focus":"motor_power"})
        interpretation=("interpret_context",dict(interpretation="Explicit part lookup",missing_fields=[],fragment_ids=["x"]))
        supervisor=("supervise",dict(route="combined",clarification="requirements"))
        review=("review",dict(decision="accept",field="requirements",reason="supported"))
        variants={"A":[get],"B":[get],"C":[interpretation,get],"D":[supervisor,interpretation,get],"E":[get,review]}
        for variant,sequence in variants.items():
            with self.subTest(variant=variant):
                workflow,store=self.workflow(sequence)
                result,_=workflow.run(variant,"Motor power for 761A00-11300000/A",[],{})
                self.assertIn("15 W",result.answer)
                self.assertEqual(len(workflow.steps),len(sequence))
                self.assertEqual(result.context["part_numbers"],["761A00-11300000/A"])

    def test_supervisor_clarifies_without_retrieval(self):
        workflow,store=self.workflow([("supervise",dict(route="clarify",clarification="requirements"))])
        result,_=workflow.run("D","Need an actuator",[],{})
        self.assertEqual(result.tool_calls[0]["name"],"ask_clarification")
        self.assertEqual(store.calls,0)

    def test_reviewer_can_block_recommendation(self):
        workflow,_=self.workflow([("get_actuator",dict(part_numbers=["761A00-11300000/A"])),
            ("review",dict(decision="clarify",field="requirements",reason="invented_requirement"))])
        result,_=workflow.run("E","Need an actuator",[],{})
        self.assertEqual(result.products,[])
        self.assertEqual(result.tool_calls[0]["name"],"ask_clarification")

    def test_history_isolation_and_lookup_followup(self):
        workflow,_=self.workflow([("get_actuator",dict(part_numbers=["764B00-11300000/A"],focus="torque"))])
        original={"part_numbers":["764B00-11300000/A"]}
        result,_=workflow.run("B","And its torque?",[{"role":"user","content":"764B00-11300000/A"}],original)
        self.assertEqual(original,{"part_numbers":["764B00-11300000/A"]})
        self.assertIn("1100",result.answer)


if __name__ == "__main__":
    unittest.main()
