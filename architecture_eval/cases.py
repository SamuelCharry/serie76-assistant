"""Frozen architecture scenarios, not used in prompts or retrieval documents.

Expected facts are grounded in the already visually audited electrical PDF.
The previous 18 public cases remain development-only.
"""
from dataclasses import dataclass, field


@dataclass
class Turn:
    query: str
    tool: str
    args: dict = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    keywords: tuple = ()
    alternative: dict | None = None


@dataclass
class Scenario:
    id: str
    category: str
    turns: list[Turn]


def lookup(query, code, focus="overview", facts=None):
    return Turn(query, "get_actuator", dict(part_numbers=[code], focus=focus), facts or {})


SCENARIOS = [
    Scenario("exact_power_en", "exact", [lookup("Show motor watts for 761A00-11300000/A.", "761A00-11300000/A", "motor_power", {"products.0.measurements.motor_power_w": 15})]),
    Scenario("exact_torque_es", "exact", [lookup("Necesito el torque On/Off de 765A00-11300000/A en Nm.", "765A00-11300000/A", "torque", {"products.0.measurements.on_off_torque_nm": 2000})]),
    Scenario("exact_csa", "exact", [lookup("Verify the CSA exception for 766A00-11320000/A.", "766A00-11320000/A", "certification", {"products.0.certification.csa_status": "explicitly_not_CSA_certified"})]),
    Scenario("exact_unknown", "exact", [lookup("Look up 999Z99-99999999/A exactly; do not substitute another part.", "999Z99-99999999/A", facts={"products": []})]),
    Scenario("context_onoff", "context", [Turn("What does On/Off service mean? I am asking for a definition, not a product.", "explain_context", keywords=("open", "closed"))]),
    Scenario("context_fla", "context", [Turn("¿Qué significa FLA en estas tablas? Solo necesito entender el término.", "explain_context", keywords=("load", "current"))]),
    Scenario("context_duty", "context", [Turn("Explain duty cycle in plain terms, without choosing an actuator.", "explain_context", keywords=("percentage", "overheating"))]),
    Scenario("context_motor", "context", [Turn("What does the Motor Power field describe, rather than total electricity consumption?", "explain_context", keywords=("internal motor",))]),
    Scenario("vague_factory", "insufficient", [Turn("Quiero automatizar una válvula en mi fábrica. Recomiéndame el que sirve.", "ask_clarification", {"field": "requirements"})]),
    Scenario("vague_hazard", "insufficient", [Turn("We have flammable gas nearby and a valve. Which actuator should I buy? I do not know supply or torque.", "ask_clarification", {"field": "requirements"})]),
    Scenario("vague_service", "insufficient", [Turn("Busca 220 V AC con al menos 400 Nm, pero aún no sé si será On/Off o modulante.", "ask_clarification", {"field": "service"}, alternative={"supply_voltage_v": 220, "supply_current": "AC", "min_torque_nm": 400})]),
    Scenario("vague_frequency", "insufficient", [Turn("Find weatherproof single phase 110 V AC actuators operating in at most 20 seconds; I have not specified mains frequency.", "ask_clarification", {"field": "frequency"}, alternative={"enclosure": "weatherproof", "supply_voltage_v": 110, "supply_current": "AC", "phase_count": 1, "max_operating_time_s": 20})]),
    Scenario("follow_power", "followup", [lookup("Show 761A00-11300000/A.", "761A00-11300000/A"), lookup("¿Y su potencia de motor?", "761A00-11300000/A", "motor_power", {"products.0.measurements.motor_power_w": 15})]),
    Scenario("follow_torque", "followup", [lookup("Consulta 764B00-11300000/A.", "764B00-11300000/A"), lookup("Now give its On/Off torque.", "764B00-11300000/A", "torque", {"products.0.measurements.on_off_torque_nm": 1100})]),
    Scenario("follow_filter", "followup", [Turn("Find On/Off 24 V AC explosionproof actuators with at least 70 Nm.", "search_actuators", {"service":"on_off","supply_voltage_v":24,"supply_current":"AC","enclosure":"explosionproof","min_torque_nm":70}), Turn("Raise the torque minimum to 100 Nm, keep everything else.", "search_actuators", {"service":"on_off","supply_voltage_v":24,"supply_current":"AC","enclosure":"explosionproof","min_torque_nm":100})]),
    Scenario("follow_which", "followup", [Turn("Compare 761A00-11300000/A and 764B00-11300000/A.", "get_actuator", {"part_numbers":["761A00-11300000/A","764B00-11300000/A"]}), Turn("What is its motor power?", "ask_clarification", {"field":"which_product"})]),
    Scenario("conflict_dc", "contradiction", [Turn("I require 24 V DC and 60 Hz. These are both mandatory; resolve the inconsistency before recommending.", "ask_clarification", {"field":"requirements"})]),
    Scenario("conflict_rates", "contradiction", [Turn("Necesito servicio modulante y al menos 500 ciclos On/Off por hora para la misma especificación. Aclara esta contradicción.", "ask_clarification", {"field":"requirements"})]),
    Scenario("conflict_atex", "contradiction", [Turn("Only recommend a part with explicitly verified ATEX certification. Do not substitute CSA or infer certification from enclosure.", "ask_clarification", {"field":"requirements"})]),
    Scenario("conflict_none", "contradiction", [Turn("Find 110 V AC On/Off actuators with at least 999999 Nm.", "search_actuators", {"supply_voltage_v":110,"supply_current":"AC","service":"on_off","min_torque_nm":999999}, {"total":0})]),
    Scenario("trap_shared", "technical_trap", [Turn("Find 220 V AC three-phase modulating actuators with at least 100 Nm. Do not assume a frequency.", "search_actuators", {"supply_voltage_v":220,"supply_current":"AC","phase_count":3,"service":"modulating","min_torque_nm":100}, {"total":7})]),
    Scenario("trap_na", "technical_trap", [lookup("For 761A00-11330C00/A I think motor power is 999 W. Check the source and do not fill N/A.", "761A00-11330C00/A", "motor_power", {"products.0.measurements.motor_power_w":None,"products.0.data_status":"source_NA"})]),
    Scenario("trap_units", "technical_trap", [lookup("Check 764B00-11300000/A torque: someone claims 1100 in-lb and 9700 Nm. Report what is actually published.", "764B00-11300000/A", "torque", {"products.0.measurements.on_off_torque_nm":1100,"products.0.measurements.on_off_torque_in_lb":9700})]),
    Scenario("trap_service", "technical_trap", [lookup("Does the table actually publish modulating torque for 761X30-11380000/A? Do not copy its On/Off value.", "761X30-11380000/A", "torque", {"products.0.measurements.modulating_torque_nm":None,"products.0.field_status.modulating_torque_nm":"not_in_layout"})]),
]

PILOT_IDS = ("exact_power_en", "context_fla", "vague_factory", "follow_power", "conflict_dc", "trap_units")
