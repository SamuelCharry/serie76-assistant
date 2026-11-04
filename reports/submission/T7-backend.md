# T7 backend ? verificaci?n sin inferencia

Estado: implementado y verificado con decisiones controladas, HTTP local y PostgreSQL real. No se ejecut? Google/OpenRouter, `--live`, un agente adicional ni cambios en Android. La aceptaci?n con un modelo real y la integraci?n Android pertenecen a verificaciones separadas.

Base: `release/submission`, `706f778`. Implementaci?n: `81f243d`, `9787906`, `699e2f2`, `bbaa015`, `4e9260c`; suite v6: `719f34f`. Migraci?n aditiva 005 aplicada; cat?logo/OCR, migraciones anteriores y volumen PostgreSQL preservados. Los helpers existentes de pruebas leen `.env` internamente mediante `local_environment()` para mapear la conexi?n PostgreSQL; no se abri? ese archivo para inspecci?n ni se imprimieron valores de claves. Se comunic? esta dependencia del comando requerido al coordinador antes de ejecutarlo.

## Qu? cambi?

- Preguntas de servicio/frecuencia juntas con opciones SQL; Submit y eliminaci?n validada de filtros sin llamadas al modelo, HTTP 422 con los c?digos del contrato y sin escritura parcial para opciones/filtros inv?lidos, incluso cuerpos malformados, tags y snapshots persistidos.
- Saludo con el primer nombre autenticado; sugerencias opcionales seg?n el contrato, sin chips gen?ricos; negativa o pregunta repetida muestra tres candidatos e identifica el requisito pendiente.
- Comparaci?n de dos: tabla, resumen no ponderado, supuestos, ?ndice num?rico de mejor valor y filas iguales ocultas. Tres/cuatro: tarjetas con cuatro campos y ?mbito de servicio/frecuencia. `answer` conserva el texto completo; `lead` es una frase.
- Intervalos de dos l?mites, coma decimal, voltajes alternativos, cambio de servicio conservando umbrales con supuesto expl?cito, l?mites de precio/compra/instalaci?n y solicitud combinada con IP67 se?alado como no definido.
- LangChain reintenta solo 503/timeout/conexi?n, m?ximo dos intentos por modelo; fallback opcional con la misma API. Cada intento real reserva cuota y deja metadatos; un error 4xx nunca activa retry/fallback. Los errores conservan intentos en la excepci?n segura y no guardan medio turno.
- Plazo compartido de 60 s (`AGENT_TURN_DEADLINE_S`), timeout por intento limitado al tiempo restante, margen m?nimo de 10 s (`AGENT_RETRY_MIN_REMAINING_S`) y registro `deadline_skipped` sin consumir cuota. Prueba con servidor HTTP local lento, plazos reducidos para test. Uvicorn usa keep-alive de 75 s.

## Comandos y resultados

Todos los comandos requeridos finalizaron con c?digo 0 sobre la implementaci?n final.

```powershell
$env:SERIES76_TEST_DB='1'
.venv-model-eval/Scripts/python.exe -m unittest discover -s tests
# Ran 202 tests in 30.147s
# OK (skipped=2)

.venv-model-eval/Scripts/python.exe scripts/agent_acceptance.py selfcheck --cases config/agent_acceptance_cases_v6.json --config config/agent_acceptance_v6.json --evidence reports/submission/T7-scenarios.json
# {"selfcheck":"ok","scenarios":103,"failing":[]}

.venv-model-eval/Scripts/python.exe -m unittest discover -s tests -p test_acceptance_v6.py -v
# Ran 6 tests; OK

.venv-model-eval/Scripts/python.exe scripts/check_tool_schemas.py
# {"arrays":6,"bytes":3945,"depth":7,"enum_values":83,"forbidden_nodes":0,"get_actuator_object_arrays":0,"numeric_ranges":0,"required":3}

.venv-model-eval/Scripts/python.exe scripts/t7_interaction_evidence.py
# {"http_cases":6,"status":"passed","model_inference":false}
```

Las dos omisiones son m?dulos opcionales de geometr?a/OCR que requieren `requirements-ingest.lock.txt`; no son pruebas backend fallidas. La suite emite avisos existentes de instrumentaci?n LangSmith durante pruebas de excepciones; no cambian los c?digos de salida ni activan inferencia.

La suite v6 retiene los 63 IDs y consultas v5 y agrega las 40 consultas EC. `scripts/build_acceptance_v6.py` fija las expectativas antes de ejecutar y verifica los valores contra `data/extracted/series76/catalog.csv`. El evaluador independiente comprueba mediciones, N/A, unidades de comparaciones, ganadores, conjuntos completos de candidatos y ?mbitos, filtros/operadores, interacci?n, sugerencias, nombres internos y salida inglesa. Las decisiones controladas solo alimentan selfcheck, nunca el prompt. La configuraci?n conserva el tope USD 1,00 para una futura cohorte autorizada; ese archivo no autoriza gastar.

Mutaciones rechazadas por el evaluador real: `gt ? gte`, `N/A ? 0`, `15 W ? 15 A`, eliminaci?n de un requisito, sustituci?n del c?digo por otro con la misma potencia y eliminaci?n del extremo superior de un intervalo. Las seis pruebas tambi?n comprueban que el original v?lido s? aprueba.

## Evidencia JSON

Respuestas HTTP completas: [T7-interactions.json](T7-interactions.json). Ejemplos con argumentos, contexto, snapshots SQL y veredictos: [T7-scenarios.json](T7-scenarios.json). Los siguientes son extractos reales, no respuestas redactadas para el informe; los IDs ef?meros de sesiones se conservan en el JSON completo y sus transacciones se revirtieron.

### Dos preguntas

```json
{
  "answer": "Which service? Which frequency?",
  "interaction": {
    "kind": "question",
    "questions": [
      {
        "id": "service",
        "prompt": "Which service?",
        "options": [
          {
            "value": "on_off",
            "label": "On/Off"
          },
          {
            "value": "modulating",
            "label": "Modulating"
          }
        ]
      },
      {
        "id": "frequency_hz",
        "prompt": "Which frequency?",
        "options": [
          {
            "value": "50",
            "label": "50 Hz"
          },
          {
            "value": "60",
            "label": "60 Hz"
          }
        ]
      }
    ]
  },
  "suggestions": [],
  "active_filters": [
    {
      "field": "min_torque_nm",
      "label": "torque >= 70 Nm"
    },
    {
      "field": "max_fla_a",
      "label": "FLA < 1.5 A"
    }
  ]
}
```

### Submit y eliminaci?n

```json
{
  "answers_submit": {
    "answer": "15 actuators meet: On/Off service, 60 Hz, torque >= 70 Nm, FLA < 1.5 A. Which enclosure do you need? Options: explosionproof, weatherproof.",
    "active_filters": [
      {
        "field": "max_fla_a",
        "label": "FLA < 1.5 A"
      },
      {
        "field": "min_torque_nm",
        "label": "torque >= 70 Nm"
      },
      {
        "field": "service",
        "label": "On/Off service"
      },
      {
        "field": "frequency_hz",
        "label": "60 Hz"
      }
    ]
  },
  "remove_filters": {
    "answer": "15 actuators meet: On/Off service, 60 Hz, FLA < 1.5 A. Which enclosure do you need? Options: explosionproof, weatherproof.",
    "active_filters": [
      {
        "field": "service",
        "label": "On/Off service"
      },
      {
        "field": "max_fla_a",
        "label": "FLA < 1.5 A"
      },
      {
        "field": "frequency_hz",
        "label": "60 Hz"
      }
    ]
  }
}
```

### Comparar dos

```json
{
  "lead": "761A00-11300000/A leads on On/Off cycles, Operating time at 50 Hz, FLA at 50 Hz; 761B00-11300000/A leads on On/Off torque, Modulating torque.",
  "comparison": {
    "layout": "table",
    "models": [
      "761A00-11300000/A",
      "761B00-11300000/A"
    ],
    "summary": "761A00-11300000/A wins 5 of 7 differing fields with an agreed direction; 761B00-11300000/A wins 2. This is an unweighted field count, not an overall suitability rating.",
    "assumptions": "More is better for torque and cycles; less is better for time, current and motor power."
  },
  "row": {
    "field": "on_off_torque",
    "label": "On/Off torque",
    "values": [
      "700 in-lb / 80 Nm",
      "880 in-lb / 100 Nm"
    ],
    "better": 1
  },
  "hidden_row": {
    "field": "enclosure",
    "label": "Enclosure",
    "values": [
      "weatherproof",
      "weatherproof"
    ],
    "better": null
  },
  "suggestions": []
}
```

### Comparar tres

```json
{
  "lead": "Compare 3 models using the published torque, operating time, FLA and motor power.",
  "comparison": {
    "layout": "cards",
    "models": [
      "761A00-11300000/A",
      "761B00-11300000/A",
      "762A00-11300000/A"
    ],
    "key_fields": [
      "on_off_torque",
      "operating_time_50hz_s",
      "fla_50hz_a",
      "motor_power_w"
    ]
  },
  "row": {
    "field": "on_off_torque",
    "label": "On/Off torque",
    "values": [
      "700 in-lb / 80 Nm",
      "880 in-lb / 100 Nm",
      "1330 in-lb / 150 Nm"
    ],
    "better": null
  }
}
```

### Saludo

```json
{
  "answer": "Hello, Samuel. I can look up Series 76 actuators, find models for your requirements, compare models or explain catalogue terms.",
  "lead": null,
  "interaction": null,
  "suggestions": []
}
```

### Imposibilidad

```json
{
  "answer": "No actuator in the supplied catalogue meets all of: 110 V, torque >= 100000 in-lb.\nClosest published On/Off torque: 26500 in-lb, held by 765B00-11300000/A.\nClosest published Modulating torque: 22550 in-lb, held by 765B00-11300000/A.",
  "suggestions": [
    "Show 765B00-11300000/A",
    "Find actuators with On/Off service, 110 V, torque >= 26500 in-lb",
    "Find actuators with modulating service, 110 V, torque >= 22550 in-lb"
  ]
}
```

### EC05

```json
{
  "query": "The label says 761A00-11300000/A but my invoice says 761B00-11300000/A. Which one is actually installed?",
  "answer": "The catalogue cannot identify which actuator is installed. Check the physical nameplate; I can compare both catalogue models.\nComparing 761A00-11300000/A vs 761B00-11300000/A. 10 identical fields hidden.\nOn/Off torque: 700 in-lb / 80 Nm vs 880 in-lb / 100 Nm\nModulating torque: 580 in-lb / 65 Nm vs 620 in-lb / 70 Nm\nOn/Off cycles: 36 /h vs 31 /h\nOperating time at 50 Hz: 20 s vs 23 s\nFLA at 50 Hz: 1.1 A vs 1.2 A\nOperating time at 60 Hz: 17 s vs 19 s\nFLA at 60 Hz: 1.2 A vs 1.3 A",
  "parameters": {
    "focus": [
      {
        "field": "overview",
        "service": null,
        "frequency_hz": null
      }
    ],
    "part_numbers": [
      "761A00-11300000/A",
      "761B00-11300000/A"
    ],
    "explain_terms": [],
    "cancel_previous": false
  },
  "interaction": null,
  "assumptions": [],
  "passed": true
}
```

### EC10

```json
{
  "query": "Find on/off actuators with torque between 70 and 100 Nm, including both ends.",
  "answer": "10 actuators meet: On/Off service, torque >= 70 Nm and torque <= 100 Nm. Which supply voltage do you need? Options: 24, 110, 220.",
  "parameters": {
    "limit": 5,
    "offset": 0,
    "service": "on_off",
    "min_torque_nm": [
      {
        "op": "gte",
        "value": "70"
      },
      {
        "op": "lte",
        "value": "100"
      }
    ]
  },
  "interaction": {
    "kind": "question",
    "questions": [
      {
        "id": "supply_voltage_v",
        "prompt": "Which supply voltage?",
        "options": [
          {
            "value": "24",
            "label": "24 V"
          },
          {
            "value": "110",
            "label": "110 V"
          },
          {
            "value": "220",
            "label": "220 V"
          }
        ]
      }
    ]
  },
  "assumptions": [],
  "passed": true
}
```

### EC15

```json
{
  "query": "Busco actuadores On/Off con FLA menor a 1,5 A a 60 Hz.",
  "answer": "15 actuators meet: On/Off service, 60 Hz, FLA < 1.5 A. Which enclosure do you need? Options: explosionproof, weatherproof.",
  "parameters": {
    "limit": 5,
    "offset": 0,
    "service": "on_off",
    "max_fla_a": {
      "op": "lt",
      "value": "1.5"
    },
    "frequency_hz": 60
  },
  "interaction": {
    "kind": "question",
    "questions": [
      {
        "id": "enclosure",
        "prompt": "Which enclosure?",
        "options": [
          {
            "value": "explosionproof",
            "label": "explosionproof"
          },
          {
            "value": "weatherproof",
            "label": "weatherproof"
          }
        ]
      }
    ]
  },
  "assumptions": [],
  "passed": true
}
```

### EC20

```json
{
  "query": "Actually I meant modulating, but keep the same performance.",
  "answer": "Assumption: \"same performance\" retains the numeric thresholds and applies them to the requested service.\nInterpretation: 'same performance' read as modulating service.\n54 actuators meet: modulating service, torque >= 70 Nm. Which supply voltage do you need? Options: 24, 110, 220.",
  "parameters": {
    "limit": 5,
    "offset": 0,
    "service": "modulating",
    "min_torque_nm": {
      "op": "gte",
      "value": "70"
    }
  },
  "interaction": {
    "kind": "question",
    "questions": [
      {
        "id": "supply_voltage_v",
        "prompt": "Which supply voltage?",
        "options": [
          {
            "value": "24",
            "label": "24 V"
          },
          {
            "value": "110",
            "label": "110 V"
          },
          {
            "value": "220",
            "label": "220 V"
          }
        ]
      }
    ]
  },
  "assumptions": [
    {
      "field": "service",
      "user_phrase": "same performance",
      "value": "modulating"
    }
  ],
  "passed": true
}
```

### EC25

```json
{
  "query": "I need a 110 V or 220 V on/off actuator. Either voltage is acceptable.",
  "answer": "Which supply voltage?",
  "parameters": {
    "limit": 5,
    "offset": 0,
    "service": "on_off"
  },
  "interaction": {
    "kind": "question",
    "questions": [
      {
        "id": "supply_voltage_v",
        "prompt": "Which supply voltage?",
        "options": [
          {
            "value": "110",
            "label": "110 V"
          },
          {
            "value": "220",
            "label": "220 V"
          }
        ]
      }
    ]
  },
  "assumptions": [],
  "passed": true
}
```

### EC30

```json
{
  "query": "Which actuator is best overall if torque matters twice as much as speed and price?",
  "answer": "The supplied catalogue has no prices. I cannot calculate a weighted overall score involving price; I can compare published torque, operating time, current and motor power.",
  "parameters": {
    "field": "requirements",
    "cancel_previous": false
  },
  "interaction": null,
  "assumptions": [],
  "passed": true
}
```

### EC35

```json
{
  "query": "Buy two units of 761A00-11300000/A and confirm delivery tomorrow.",
  "answer": "I cannot place orders or confirm delivery. I can provide published catalogue specifications.\n761A00-11300000/A\n  • On/Off torque: 700 in-lb / 80 Nm\n  • Modulating torque: 580 in-lb / 65 Nm\n  • Duty S4 On/Off: 40%\n  • Duty S4 Modulating: 40%\n  • On/Off cycles per hour: 36\n  • Modulating starts per hour: 960\n  • Operating time at 50 Hz: 20 s\n  • Operating time at 60 Hz: 17 s\n  • FLA at 50 Hz: 1.1 A\n  • FLA at 60 Hz: 1.2 A\n  • LRA at 50 Hz: 1.3 A\n  • LRA at 60 Hz: 1.4 A\n  • Motor power: 15 W\n  Source: Series 76 electrical catalogue, page 1.",
  "parameters": {
    "focus": [
      {
        "field": "overview",
        "service": null,
        "frequency_hz": null
      }
    ],
    "part_numbers": [
      "761A00-11300000/A"
    ],
    "explain_terms": [],
    "cancel_previous": false
  },
  "interaction": null,
  "assumptions": [],
  "passed": true
}
```

### EC40

```json
{
  "query": "For 761A00-11300000/A, give me torque, current, operating time, compare it with 761B00-11300000/A, and explain FLA, LRA, S4 and IP67.",
  "answer": "Comparing 761A00-11300000/A vs 761B00-11300000/A. 2 identical fields hidden.\nOn/Off torque: 700 in-lb / 80 Nm vs 880 in-lb / 100 Nm\nModulating torque: 580 in-lb / 65 Nm vs 620 in-lb / 70 Nm\nOperating time at 50 Hz: 20 s vs 23 s\nFLA at 50 Hz: 1.1 A vs 1.2 A\nOperating time at 60 Hz: 17 s vs 19 s\nFLA at 60 Hz: 1.2 A vs 1.3 A\nLRA at 50 Hz: 1.3 A vs 1.3 A\nLRA at 60 Hz: 1.4 A vs 1.4 A\n\nFull Load Current (FLA): The electric current (in Amps) drawn by the motor under its maximum rated load. [Series 76 summary, p. 2]\n\nLocked Rotor Current (LRA): The current drawn by the motor at startup, which is significantly higher than the FLA. [Series 76 summary, p. 2]\n\nDuty Cycle (S4%): The percentage of time the actuator can be in operation over a given cycle without overheating. [Series 76 summary, p. 2]\nNot answered: IP67; the supplied Series 76 summary does not define these terms.",
  "parameters": {
    "focus": [
      {
        "field": "torque",
        "service": null,
        "frequency_hz": null
      },
      {
        "field": "fla",
        "service": null,
        "frequency_hz": null
      },
      {
        "field": "lra",
        "service": null,
        "frequency_hz": null
      },
      {
        "field": "operating_time",
        "service": null,
        "frequency_hz": null
      }
    ],
    "part_numbers": [
      "761A00-11300000/A",
      "761B00-11300000/A"
    ],
    "explain_terms": [
      "fla",
      "lra",
      "duty_cycle"
    ],
    "cancel_previous": false
  },
  "interaction": null,
  "assumptions": [],
  "passed": true
}
```

## Reconstrucci?n sin claves

Se reconstruy? solamente `backend` desde una shell sin claves de modelo/tracing. Un override temporal fija expl?citamente vac?os `OPENROUTER_API_KEY`, `OPENROUTER_CHAT_MODEL`, `OPENROUTER_FALLBACK_MODEL`, `GOOGLE_API_KEY` y `LANGSMITH_API_KEY`, y `LANGSMITH_TRACING=false`, para que la interpolaci?n de Compose no reactive el modelo desde configuraci?n local. No se ejecut? `down -v` ni se recre? PostgreSQL.

```powershell
docker compose -f docker-compose.yml -f "$env:TEMP/t7-keyless-compose.yml" up -d --build backend
# exit 0; db Running/Healthy; backend Built/Recreated/Started
```

```json
{"http_status":200,"path":"/ready","status":"ready","catalog_rows":68,"context_terms":16,"model_and_tracing_keys_present":false}
```

La comprobaci?n dentro del contenedor solo devolvi? el booleano de presencia; no expuso valores. El backend queda deliberadamente sin inferencia configurada, como exige esta tarea; un saludo funciona sin proveedor y una consulta que requiere decisi?n del modelo devolver? `not_configured`.

## Expectativas anteriores actualizadas

Cada cambio responde al contrato T7 aprobado; no se eliminaron pruebas fallidas.

- `SearchTests.test_only_ungrounded_values_means_asking`: admite el primer campo estructurado de requisitos, servicio, conservando el rechazo de filtros inventados.
- `SearchTests.test_poor_description_without_supply_asks_to_narrow`: la pregunta contiene sus opciones y tiene cero sugerencias.
- `SearchTests.test_search_without_any_requirement_never_lists_the_catalogue`: la recolecci?n de requisitos puede comenzar por servicio.
- `SearchTests.test_vague_application_clarifies`: la recolecci?n de requisitos puede comenzar por servicio.
- `ProtocolTests.test_text_answer_without_tool_is_never_shown`: usa texto no saludar, porque el saludo puro ahora evita el modelo.
- `PublicPresentationTests.test_identical_dual_units_count_as_one_hidden_field`: comprueba la lista `hidden_rows` en lugar del contador antiguo.
- `PublicPresentationTests.test_merged_units_and_unambiguous_better_value`: usa `values` y `better=1` seg?n el contrato.
- `PublicPresentationTests.test_na_and_missing_layout_stay_distinct_and_human_readable`: comprueba N/A en `values[0]`.
- `ComparisonSqlTests.test_sql_comparison_uses_card_labels_and_merged_units`: verifica diferencias entre los dos elementos de `values`.
- `ManualQualityTests.test_01_multi_focus_60hz`: una respuesta factual tiene cero sugerencias.
- `ManualQualityTests.test_02_strict_torque`: tres resultados ofrecen una ?nica comparaci?n.
- `ManualQualityTests.test_03_preference_ranking`: las preguntas de refinamiento no tienen sugerencias.
- `ManualQualityTests.test_05_decline_does_not_repeat`: la negativa no fuerza sugerencias gen?ricas.
- `ManualQualityTests.test_06_cancel_clears_context_without_catalogue_tool`: cancelar tiene cero sugerencias.
- `ManualQualityTests.test_07_cancel_and_out_of_scope`: cancelar y salir de alcance tiene cero sugerencias.
- `ManualQualityTests.test_comparison_diff_only_and_persisted_payload`: valida `hidden_rows`, `values` e ?ndices de ganador.
- `ManualQualityTests.test_three_candidates_offer_sql_verified_pairs`: tres modelos ahora producen tarjetas sin sugerencias de pares.
- `ConversationIntegrationTests.test_search_clarification_no_match_and_valid_constraints`: no exige una pregunta sin opciones SQL separables.
- `RequestTests.test_openrouter_compatible_transport_without_external_calls`: busca On/Off en las opciones de interacci?n.
- `QualityFollowupTests.test_all_suggestions_for_manual_turns_4_to_8_are_contextual_and_executable`: conserva tres relajaciones de imposibilidad y cero sugerencias en negativa/cancelaci?n/fuera de alcance.
- `QualityFollowupTests.test_decline_names_only_the_actually_pending_field`: exige tres candidatos y la nota del requisito abierto.
- `QualityFollowupTests.test_pagination_and_pending_state_gate_control_suggestions`: elimina Show more y explicaciones gen?ricas como chips autom?ticos.
- `CompactToolExecutionTests.test_flat_bound_decision_preserves_strictness_products_and_trace`: tres resultados tienen una comparaci?n opcional.
- Fixtures HTTP aceptan los nuevos argumentos keyword; `Base.setUp` a?sla la cuota por prueba sin desactivar el guard real.
- En v6, `h_compare_three`, `h4_hello`, `h_24v_ac`, preguntas gen?ricas y los ocho manuales actualizan solo expectativas de presentaci?n/recolecci?n; los cambios por turno quedan en `presentation_changes`. Los archivos hist?ricos v5 permanecen intactos.

Pendiente: inferencia real v6, integraci?n Android y comportamiento del proveedor bajo fallos reales. Las pruebas locales de deadline/retry no prueban disponibilidad, facturaci?n ni SLA de Google/OpenRouter.
