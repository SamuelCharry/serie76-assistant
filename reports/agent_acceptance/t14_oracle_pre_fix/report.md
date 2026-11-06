# T14 Plan B oracle baseline

Baseline: e90c397. Scripted ideal decisions against real PostgreSQL; embeddings and inference disabled.

7/42 scenarios passed; exit 1. New fields are deliberately rejected by the pre-fix schema. This measures code/contract behavior, not generalization.

Two new paraphrases per failure class; related v13 failures share a class. All v13 failures are diagnostic. Provider tail latency is not reproduced by this offline oracle.

- T14_search_priority_1: failed; state frequency_hz: None != 60; active filter missing: frequency_hz; winner does not optimize the requested published metric; ranking label does not describe the applied priority
- T14_search_priority_2: failed; state frequency_hz: None != 60; active filter missing: frequency_hz; winner does not optimize the requested published metric; ranking label does not describe the applied priority
- T14_shown_priority_1: failed; no explicit selection from the shown models; winner does not optimize the requested published metric; ranking label does not describe the applied priority
- T14_shown_priority_2: failed; no explicit selection from the shown models; winner does not optimize the requested published metric; ranking label does not describe the applied priority
- T14_torque_priority_1: failed; no explicit selection from the shown models; winner does not optimize the requested published metric; ranking label does not describe the applied priority
- T14_torque_priority_2: failed; unrequested answer concept: delivery times; no explicit selection from the shown models; winner does not optimize the requested published metric; ranking label does not describe the applied priority
- T14_warranty_1: failed; published specifications not shown
- T14_warranty_2: failed; published specifications not shown
- T14_mounting_1: failed; published specifications not shown; missing answer concept: The catalogue does not publish bolt pattern
- T14_mounting_2: failed; published specifications not shown; missing answer concept: The catalogue does not publish bolt pattern
- T14_voltage_hyphen_1: failed; state supply_voltage_v: None != 110; active filter missing: supply_voltage_v; already stated/removed field asked: supply_voltage_v
- T14_voltage_hyphen_2: failed; state supply_voltage_v: None != 110; active filter missing: supply_voltage_v; already stated/removed field asked: supply_voltage_v
- T14_keep_voltage_1: failed; no matching products shown
- T14_keep_voltage_2: failed; no matching products shown
- T14_keep_quantity_1: failed; no matching products shown
- T14_keep_quantity_2: failed; no matching products shown
- T14_keep_impossible_1: failed; missing answer concept: No actuator
- T14_keep_impossible_2: failed; missing answer concept: No actuator
- T14_keep_dc_exclusion_1: failed; no matching products shown
- T14_keep_dc_exclusion_2: failed; no matching products shown
- T14_spanish_service_1: failed; state dc_only: None != True; active filter missing: dc_only
- T14_spanish_service_2: failed; state supply_current: None != 'DC'; active filter missing: supply_current; state dc_only: None != True; active filter missing: dc_only
- T14_contradiction_1: passed; 
- T14_contradiction_2: passed; 
- T14_capabilities_1: passed; 
- T14_capabilities_2: passed; 
- T14_na_explanation_1: failed; missing answer concept: N/A; missing answer concept: not published|not available|source
- T14_na_explanation_2: failed; missing answer concept: N/A; missing answer concept: not published|not available|source
- T14_single_reference_1: passed; 
- T14_single_reference_2: passed; 
- T14_safe_site_1: failed; cleared hazard still active
- T14_safe_site_2: passed; 
- T14_site_question_1: failed; missing answer concept: Weatherproof; missing answer concept: Explosionproof; missing answer concept: confirm|classification
- T14_site_question_2: failed; missing answer concept: Weatherproof; missing answer concept: Explosionproof; missing answer concept: confirm|classification
- T14_supply_overview_1: failed; missing answer concept: 24; missing answer concept: 110; missing answer concept: 220; missing answer concept: AC; missing answer concept: DC
- T14_supply_overview_2: failed; missing answer concept: 24; missing answer concept: 110; missing answer concept: 220; missing answer concept: AC; missing answer concept: DC
- T14_compound_overview_1: failed; missing answer concept: Weatherproof; missing answer concept: Explosionproof
- T14_compound_overview_2: failed; missing answer concept: 24; missing answer concept: 110; missing answer concept: 220; missing answer concept: Weatherproof; missing answer concept: Explosionproof
- T14_scoped_service_overview_1: failed; missing answer concept: DC; missing answer concept: AC/DC; missing answer concept: Modulating; missing answer concept: On/Off
- T14_scoped_service_overview_2: failed; missing answer concept: DC; missing answer concept: AC/DC
- T14_retain_site_refinement_1: failed; no matching products shown
- T14_retain_site_refinement_2: failed; no matching products shown
