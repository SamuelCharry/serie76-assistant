# SV2 v7 differences

**353/453 passed (77.92%); the >=95% target failed.** Baseline v1: 453/453. No inference was run.

Classification unit: one failed conversation, not one assertion. Class (iii) takes precedence in mixed cases. A rejected fixture is a regression of this delivered offline path when it prevents a previously supported answer; a correct validator does not excuse an inadequate converter. These classifications do not establish live-model performance or authorize adoption.

- **(i) Intentional contract differences:** one model call instead of a deterministic fast path, or an explicitly stricter number/unit grounding question.
- **(ii) Legacy presentation/question-format gaps:** the requested fact, correct empty result, or safe refusal is present, but wording, focus, or structured representation differs. These still fail the frozen gate and need product acceptance.
- **(iii) Genuine regressions:** wrong or missing answers, lost requirements/priorities, broken controls, or unresolved safety/scope. Includes converter limitations; root cause is not assumed to be the live model.

**Counts: (i) 7; (ii) 36; (iii) 57; total 100.**

Review used the actual response, state trace and failed assertions. Examples: a formatting assertion in R1-02 masks a lost current priority; Q3-04 also contains a rejected valid UI answer. They are class (iii). An unsupported single-topic request answered as unpublished information is class (ii) only when no figure or compatibility claim is invented.

Per coordinator instruction, no repairs or expectation changes were started after this classification request. Paid v15 A/B remains pending; adoption remains blocked.

| # | Scenario | Class | Explanation | Frozen failed assertions |
|---|---|---|---|---|
| 1 | exact_unknown | (iii) | A complete unknown code gets another complete-code question instead of an explicit SQL not-found answer. | tool ask_clarification != get_actuator; missing text: 769Z99-11300000/A is not in the supplied Series 76 electrical catalogue |
| 2 | exact_partial | (ii) | The incomplete code correctly triggers clarification; the legacy exact phrase about a complete Base Part Number is absent. | missing text: not a complete Base Part Number |
| 3 | conflict_dc_60hz | (iii) | The DC/frequency contradiction is lost and the replay shows products instead of asking to resolve it. | conflict None != dc_frequency; unexpected products ['761X30-11370000/A', '761X30-11380000/A', '762X30-11370000/A'] |
| 4 | conflict_rate_service | (iii) | The cycles-per-hour versus Modulating service contradiction is lost before the displayed search. | conflict None != cycles_modulating; unexpected products ['761X30-11320000/A', '761Y30-11320000/A', '761A00-11320000/A'] |
| 5 | more_results | (iii) | The requested next page does not advance; the converted view retains the first page. | offset None != 5 |
| 6 | h_prompt_leak | (ii) | The request for hidden instructions is refused; only the legacy clarification object is absent. | clarification None not in ['unsupported'] |
| 7 | t6_manual_02 | (i) | The validator rejects a converted 1000 in-lb value quoted as 1,000 In-Lbs; it does not guess grouping semantics. | tool set_conversation_state != search_actuators; enclosure None != explosionproof; supply_voltage_v None != 24; supply_current None != DC; service None != modulating; min_torque_in_lb None != {'value': 1000, 'op': 'gt'}; missing text: > 1000 in-lb; product 762X30-11370000/A missing; product 762Y30-11370000/A missing; product 763X30-11370000/A missing; product count differs; unexpected clarification |
| 8 | t6_manual_04 | (i) | The validator rejects converted 100000 from 100,000 rather than silently accepting a numeric spelling it cannot validate. | tool set_conversation_state != search_actuators; supply_voltage_v None != 110; min_torque_in_lb None != {'value': 100000, 'op': 'gte'}; missing text: No actuator; missing text: Closest published; missing text: Closest published On/Off torque: 26500 in-lb; missing text: Closest published Modulating torque: 22550 in-lb; unexpected clarification |
| 9 | t6_manual_05 | (iii) | The decline flow references products not supplied or previously shown and cannot return the requested best matches. | tool set_conversation_state != ask_clarification; field None != decline; missing text: best matches so far; product count differs; unexpected clarification |
| 10 | t6_manual_07 | (iii) | Cancellation retains filters or pending clarification and does not confirm cancellation. | missing text: Cancelled; unexpected clarification; cancel retained filters or pending clarification |
| 11 | t6_manual_08 | (iii) | Strict grouping validation also blocks the compound cancel/new-search turn; the retained old torque violates the cancellation request, so this mixed case is a regression. | tool set_conversation_state != search_actuators; supply_voltage_v None != 110; min_torque_in_lb None != {'value': 100000, 'op': 'gt'}; cancel_previous None != True; missing text: Cancelled; missing text: No actuator; missing text: Closest published; missing text: Closest published On/Off torque: 26500 in-lb; missing text: Closest published Modulating torque: 22550 in-lb; unexpected clarification; unexpected retained filter: min_torque_nm |
| 12 | EC03 | (iii) | The already complete unknown code receives a repeat code question instead of the explicit not-found answer. | tool ask_clarification != get_actuator; part_numbers None != ['769Z99-11300000/A']; missing text: not in the supplied |
| 13 | EC08 | (iii) | A current-bound correction is rejected for frequency provenance even though the earlier user turn supplied 60 Hz; the converted evidence is inadequate. | tool set_conversation_state != search_actuators; service None != on_off; frequency_hz None != 60; max_fla_a None != {'value': 1.5, 'op': 'lte'} |
| 14 | EC20 | (ii) | The service change and retained performance requirement are applied; the old same-performance wording and assumption representation are absent. | missing text: same performance; assumption missing |
| 15 | EC21 | (ii) | The vague selection request still gets a requirements question; the requested wording and question representation differ. | missing text: Tell me what it must do: |
| 16 | EC23 | (iii) | The explicit DC/60 Hz conflict is omitted and the replay returns DC products. | supply_current None != DC; frequency_hz None != 60; conflict None != dc_frequency |
| 17 | EC24 | (iii) | Declining the pending question fails instead of returning the available matches. | tool set_conversation_state != ask_clarification; field None != decline; missing text: best matches so far; product count differs; unexpected clarification |
| 18 | EC25 | (iii) | A choice restricted to 110 or 220 V exposes a 24 V option, losing the requested scope. | question options differ: supply_voltage_v |
| 19 | EC27 | (iii) | The least-energy request becomes a generic requirements question without the requested power distinction or ranking. | tool ask_clarification != catalogue_superlative; missing text: not total electrical consumption |
| 20 | EC28 | (ii) | The impossible torque correctly produces no matches; the optional closest published 9000 Nm diagnostic is missing. | missing text: 9000 Nm |
| 21 | EC30 | (ii) | Price unavailability and the inability to compute a weighted price score are stated; contraction matching and an additional question differ. | tool ask_clarification != document_limitation; missing text: doesn't publish prices; unexpected clarification |
| 22 | EC34 | (ii) | The hidden-instruction request is refused; the old unsupported clarification field is missing. | field requirements != unsupported; clarification None not in ['unsupported', 'decline'] |
| 23 | T8_recommendation | (iii) | The later valid structured voltage/enclosure answer is rejected, blocking the recommendation flow; this exceeds a question-count difference. | too few simultaneous questions; tool set_conversation_state != search_actuators; recommendation total differs; ranking explanation missing |
| 24 | T8_best_two | (ii) | A single requirements question replaces multiple simultaneous questions; the later comparison still answers correctly. | too few simultaneous questions |
| 25 | T8_which_ones | (ii) | The search supplies the models but uses one pending question and different ranked-model wording. | too few simultaneous questions; missing text: ranked models |
| 26 | T8_remove_service | (ii) | Removing the service restriction leaves a single pending question rather than the old multiple-question format. | too few simultaneous questions |
| 27 | T8_fast_compare | (i) | The correct comparison now uses one model decision instead of the v1 zero-call fast path. | debug model-call flag differs |
| 28 | T8_three_compare | (i) | The correct three-model comparison now uses one model decision instead of the v1 zero-call fast path. | debug model-call flag differs |
| 29 | T8_torque_term | (iii) | The converted glossary key is rejected and the requested supported torque explanation is omitted. | tool set_conversation_state != explain_terms |
| 30 | T8_zero | (ii) | The impossible requirement correctly yields no matches; closest-value prose and the empty recommendation representation differ. | missing text: Closest published; recommendation total differs |
| 31 | T8_rank_fastest | (iii) | The rank-fastest action produces a question instead of a ranking; a changed call count does not excuse the missing answer. | too few simultaneous questions; tool ask_clarification != ranked_action; ranking explanation missing; debug model-call flag differs |
| 32 | heldout_P1-03 | (ii) | Both requested 60 Hz operating times are present in the SQL answer/table; the lead instead summarizes other differing fields. | missing lead text: 764A00-11300000/A 30 s; missing lead text: 765A00-11300000/A 88 s |
| 33 | heldout_P6-01 | (ii) | The price limitation is correctly stated using does not rather than the frozen contraction. | missing text: doesn't publish prices |
| 34 | heldout_B-FRUSTRATION-01 | (iii) | The follow-up selection is not delivered. | missing text: I recommend |
| 35 | heldout_B-SHORTREF-01 | (iii) | The other-one reference loses the known alternative and asks for a code instead. | tool get_actuator != ranked_reference; tool ask_clarification != ranked_reference |
| 36 | heldout_v2_Q1-03 | (ii) | Both requested 60 Hz current values are present in the SQL answer/table; the compact lead does not highlight them. | missing lead text: 763B00-11300000/A 4.8 A; missing lead text: 763X30-11300000/A 2.3 A |
| 37 | heldout_v2_Q3-04 | (iii) | The conversation rejects a valid voltage/enclosure control answer before the final one-of-one result; despite a wording-only final assertion, the earlier broken interaction is substantive. | missing text: That's the only model |
| 38 | heldout_v2_Q4-03 | (iii) | The equivalent 220 V version is rejected as an ungrounded code; the replay cannot answer the requested counterpart lookup. | missing text: 761B00-11320000/A |
| 39 | heldout_v2_Q5-04 | (iii) | The Spanish follow-up selection is omitted. | missing text: I recommend |
| 40 | heldout_v2_Q5-05 | (ii) | The misspelled enclosure request is applied correctly, but there is no explicit interpretation note. | missing text: Interpreted 'explsionproof' as Explosionproof. |
| 41 | heldout_v2_Q5-06 | (i) | The converted 500 Nm value cannot be quoted from 0.5 kNm; the strict validator asks instead of accepting an unsupported unit conversion. | missing text: kNm = |
| 42 | heldout_v2_Q6-01 | (ii) | Delivery and lead-time unavailability are both stated; the exact old wording differs. | missing text: does not publish delivery times |
| 43 | heldout_v2_Q6-04 | (ii) | The request to pretend a different torque is refused without fabricated figures; the legacy explicit refusal wording is absent. | missing text: can't use other values |
| 44 | heldout_v2_C-FRUSTRATION-01 | (iii) | The follow-up pick is missing. | missing text: I recommend |
| 45 | heldout_v2_C-FRUSTRATION-02 | (iii) | A proposed pick references an unshown product and is rejected; the requested visible-set selection is missing. | missing text: I recommend |
| 46 | heldout_v2_C-SHORTREF-02 | (iii) | The faster-one recommendation and subsequent power answer are missing; zero-versus-one calls are not the material failure. | missing text: 762A00-11300000/A; debug model-call flag differs; missing text: Motor power |
| 47 | heldout_v2_C-CORRECTION-01 | (iii) | The enclosure-equivalent correction is rejected and the requested counterpart answer is missing. | missing text: 763Y30-11320000/A |
| 48 | heldout_v3_R1-01 | (ii) | The correct 960 starts/hour appears, but a full specification adds torque, duty and cycle details beyond the requested field. | forbidden text: Duty S4; forbidden text: On/Off cycles |
| 49 | heldout_v3_R1-02 | (iii) | The replay loses the user's lowest-current priority and defaults to closest torque; duplicated code strings are only the visible assertion failure. | ranked code repeated or absent in answer: 763Y30-11300000/A; ranked code repeated or absent in answer: 764X30-11300000/A; ranked code repeated or absent in answer: 764Y30-11300000/A |
| 50 | heldout_v3_R1-06 | (iii) | The counterpart comparison cannot resolve the requested alternative and is omitted. | comparison models differ; comparison layout differs |
| 51 | heldout_v3_R2-07 | (iii) | The indoors qualifier is silently ignored when returning the highest-torque pick; no unsupported-site qualification is given. | missing text: doesn't classify models as indoor |
| 52 | heldout_v3_R4-03 | (iii) | The requested 110 V equivalent is not answered. | missing text: 762X30-11300000/A; missing text: Motor power |
| 53 | heldout_v3_R5-02 | (ii) | The requested startup current is present, but full specifications include unrelated torque and power fields. | forbidden text: On/Off torque; forbidden text: Motor power |
| 54 | heldout_v3_R5-05 | (i) | The converted 1200 Nm value is rejected because the user supplied 1.2 kNm; unsupported conversion is not silently accepted. | missing text: 3-phase; missing text: 1.2 kNm = 1200 Nm |
| 55 | heldout_v3_R6-01 | (ii) | Weight unavailability is stated; only the frozen contraction differs. | missing text: doesn't publish |
| 56 | heldout_v3_R6-02 | (ii) | Wiring-information unavailability is stated, with different diagram/contraction wording. | missing text: doesn't publish; missing text: wiring diagram |
| 57 | heldout_v3_R6-03 | (ii) | The single 4-20 mA compatibility question receives a safe unpublished-information answer; the requested noun is absent, with no compatibility claim. | missing text: doesn't publish; missing text: signal compatibility |
| 58 | heldout_v3_D-TOPICJUMP-01 | (iii) | The highest-duty follow-up is not answered. | missing text: duty |
| 59 | heldout_v3_D-SHORTREF-02 | (iii) | The faster-one follow-up comparison is missing. | missing text: operating time |
| 60 | heldout_v3_D-IMPOSSIBLE-01 | (ii) | The impossible Weatherproof/24 V search returns no matches and relaxation counts; the extra explanation that 24 V is only Explosionproof is absent. | missing text: 24 V models are only Explosionproof |
| 61 | heldout_v4_S1-01 | (iii) | The requested 220 V version is missing. | missing text: 763Y30-11320000/A; missing text: Motor power |
| 62 | heldout_v4_S1-02 | (iii) | The maximum-cycles question is not answered. | missing text: 190 cycles/h |
| 63 | heldout_v4_S1-05 | (iii) | The requested LRA/FLA ratio is missing. | missing text: 1.2 A / 1 A = 1.2 |
| 64 | heldout_v4_S2-04 | (iii) | The efficiency objective is replaced by a supply question and generic limitation, without explaining what efficiency can or cannot mean in the catalogue. | missing text: efficiency |
| 65 | heldout_v4_S2-05 | (ii) | Generator compatibility receives a safe unpublished-information response; the specific generator wording is missing. | missing text: generator operation |
| 66 | heldout_v4_S3-01 | (i) | The bare 110 lacks a voltage unit; the strict provenance validator rejects the proposed voltage instead of inferring V, and later selection cannot proceed from that rejected state. | active filter missing: service; active filter missing: min_torque_nm; missing text: I recommend; missing text: Modulating torque |
| 67 | heldout_v4_S3-06 | (iii) | The next-page request repeats the page and does not give the required end-of-results answer. | missing text: No more ranked models |
| 68 | heldout_v4_S5-04 | (ii) | The lowest-current 24 V ranking is correct; the old expectation forbids the new explicit Ranked by heading. | forbidden text: Ranked by |
| 69 | heldout_v4_S6-01 | (ii) | The single IP-rating question gets an unpublished-information refusal without inventing a rating; only the specific noun/format differs. | missing text: IP rating |
| 70 | heldout_v4_S6-02 | (ii) | Maintenance-interval unavailability is conveyed generically; no invented interval is supplied. | missing text: maintenance interval |
| 71 | heldout_v4_S6-03 | (ii) | CAD availability is declined as unpublished information; only the specific CAD wording is absent. | missing text: CAD drawing |
| 72 | heldout_v4_E-SHORTREF-02 | (iii) | The duty follow-up is missing. | missing text: duty |
| 73 | heldout_v4_E-IMPOSSIBLE-01 | (iii) | After the correctly empty search, the request for an alternative gets an unrelated requirements question instead of an actionable relaxation. | missing text: Weatherproof; missing text: no exact model |
| 74 | heldout_v5_T1-05 | (iii) | The requested LRA-minus-FLA difference of 0.4 A is omitted. | missing text: 0.4 A |
| 75 | heldout_v5_T2-06 | (ii) | Price unavailability is stated and the explicit motor-power proxy is used; the failed assertion is contraction wording. | missing text: doesn't publish prices |
| 76 | heldout_v5_T4-03 | (iii) | The requested three-phase counterpart is omitted. | missing text: 763C00-11330C00/A |
| 77 | heldout_v5_T5-05 | (ii) | The maximum-50 Nm search correctly returns no matches; the additional published minimum of 65 Nm is missing. | missing text: lowest published torque is 65 Nm |
| 78 | heldout_v5_T6-01 | (ii) | The temperature question gets an unpublished-information answer with no fabricated range; the specific noun is absent. | missing text: operating temperature range |
| 79 | heldout_v5_T6-03 | (ii) | Installation information is correctly declined; inserting or wiring breaks the frozen contiguous phrase. | missing text: installation instructions |
| 80 | heldout_v6_U1-04 | (iii) | The 0.3 A current difference is missing and the response re-asks which already-known products to compare. | missing text: 1.3 A; missing text: 1 A; missing text: difference 0.3 A; forbidden text: Which of the previously listed |
| 81 | heldout_v6_U2-04 | (ii) | The lifetime question gets a safe unpublished-information answer; the specific lifetime noun and follow-up question format differ. | missing text: service life |
| 82 | heldout_v6_U2-05 | (iii) | The requested catalogue torque range of 65 to 9000 Nm is not provided. | missing text: 65; missing text: 9000; missing text: On/Off; missing text: Modulating |
| 83 | heldout_v6_U2-06 | (ii) | The 48 V search correctly returns no matches; the empty recommendation object and label differ. | recommendation total differs; ranking explanation missing |
| 84 | heldout_v6_G-REPHRASE-01 | (iii) | The vague big-valve request displays broadly ranked products without establishing the needed torque requirement. | unexpected products ['761X30-11320000/A', '761Y30-11320000/A', '761A00-11320000/A']; question ids differ |
| 85 | heldout_v6_G-TOPICJUMP-01 | (iii) | The quickest-model follow-up is missing. | missing text: operating time |
| 86 | heldout_v6_G-SHORTREF-02 | (iii) | The stronger-model reference comparison is missing. | missing text: 765Y30-11320000/A 3000 Nm; missing text: 765X30-11320000/A 2000 Nm |
| 87 | heldout_v6_G-IMPOSSIBLE-01 | (iii) | The closest-alternative request does not explain the necessary DC/three-phase relaxation. | missing text: Drop 3-phase; missing text: Drop DC |
| 88 | heldout_v6_G-CORRECTION-01 | (ii) | The corrected code is applied and the requested data remain in the full SQL answer; extra On/Off torque violates the narrow presentation expectation. | forbidden text: On/Off torque |
| 89 | heldout_v7_V1-04 | (iii) | The requested 7 s operating-time difference is missing. | missing text: difference; missing text: 7 s |
| 90 | heldout_v7_V1-05 | (iii) | The three-phase count is answered at the wrong scope, giving a voltage count of 3 instead of the requested 7. | missing text: 7; missing text: without published values |
| 91 | heldout_v7_V2-05 | (iii) | The smallest-actuator question becomes a supply-voltage question, leaving the size criterion unaddressed. | question ids differ |
| 92 | heldout_v7_V5-05 | (iii) | The Spanish lowest-motor-power request becomes a voltage question instead of answering the stated objective. | question ids differ |
| 93 | heldout_v7_V6-05 | (ii) | The manufacturer question gets a generic unpublished-information answer without an invented manufacturer; its specific noun is absent. | missing text: manufacturer |
| 94 | T9_R1_pair | (iii) | The pair recommendation is replaced by a generic requirements question; the 761A00 pick, FLA comparison and trade-off are missing. | missing text: I recommend 761A00-11300000/A; missing text: FLA at 50 Hz: 1.1 A vs 1.2 A; missing text: Choose 761B00-11300000/A only if; recommendation total differs; recommended winner differs; debug model-call flag differs |
| 95 | T9_R1_top_two | (iii) | The top-two follow-up asks generic requirements instead of selecting 762A00 with the stated 150 Nm objective. | missing text: I recommend 762A00-11320000/A; missing text: closest torque at or above 150 Nm; recommendation total differs; recommended winner differs; debug model-call flag differs |
| 96 | T9_R1_new_bound | (iii) | The new 200 Nm bound and low-current objective get a generic question; the 763A00 pick and exclusion of the 150 Nm model are missing. | missing text: I recommend 763A00-11320000/A; missing text: 762A00-11320000/A is out: On/Off torque 150 Nm < 200 Nm.; recommendation total differs; recommended winner differs; debug model-call flag differs |
| 97 | T9_R1_spanish | (iii) | The Spanish request to select among the shown models becomes a generic requirements question; no recommendation is delivered. | missing text: I recommend 761A00-11300000/A; recommendation total differs; recommended winner differs; debug model-call flag differs |
| 98 | T9_R1_list | (iii) | The shown-set low-power selection gets a generic question and a power disclaimer, but no 40 W winner or ranking. | missing text: Motor power 40 W; missing text: lowest motor power; recommendation total differs; recommended winner differs; debug model-call flag differs |
| 99 | T9_R1_tie | (iii) | The low-power request gets a generic question and a disclaimer, with no 15 W tie explanation or FLA tie-break. | missing text: The priority ties at 15 W; lowest FLA breaks the tie.; recommendation total differs; recommended winner differs; debug model-call flag differs |
| 100 | T9_R1_none | (iii) | The empty eligible shown-set case gets a generic question instead of the no-match answer and nearest shown model. | missing text: None of the shown models meets every requirement.; missing text: Nearest shown model: 761B00-11300000/A; recommendation total differs; debug model-call flag differs |
