
## L5-04  (persona: typos-mixed)
Scripted user turns: ["Necesito 24 V de corriente continua únicamente; excluye los modelos AC/DC.", "¿Cuál de los que mostraste recomendarías para abrir y cerrar?"]

### Variant A
  > USER: Necesito 24 V de corriente continua únicamente; excluye los modelos AC/DC.   [2.95 s, HTTP 200]
    ANSWER: 5 actuators meet: AC/DC, 24 V. Here are the leading published models. | Ranked by lowest FLA, then shortest operating time. | 761X30-11380000/A: Explosionproof; On/Off torque 70 Nm; FLA 5 A | 762X30-11380000/A: Explosionproof; On/Off torque 150 Nm; FLA 6 A | 761Y30-11380000/A: Explosionproof; On/Off torque 80 Nm; FLA 6.3 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    RANKED LIST: lowest FLA, then shortest operating time total=5 shown: 761X30-11380000/A, 762X30-11380000/A, 761Y30-11380000/A
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 761Y30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    CHIPS: Compare top 2 | Show all 5
    ACTIVE FILTERS: AC/DC, 24 V
  > USER: ¿Cuál de los que mostraste recomendarías para abrir y cerrar?   [0.12 s, HTTP 200]
    ANSWER: I recommend 761X30-11380000/A: Explosionproof; FLA (frequency not specified) 5 A; meets AC/DC, On/Off service, 24 V. Ranked by lowest FLA, then shortest operating time, then part number. Versus 762X30-11380000/A: FLA (frequency not specified in the source): 5 A vs 6 A; Operating time (frequency not specified in the source): 17 s vs 22 s; On/Off cycles: 350 /h vs 200 /h. Choose 762X30-11380000/A only if its On/Off torque advantage (1350 in-lb / 150 Nm vs 620 in-lb / 70 Nm) matters more than the stated priority. Assumes no torque requirement; tell me the torque you need. | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    RANKED LIST: lowest FLA, then shortest operating time, then part number total=3 shown: 761X30-11380000/A, 762X30-11380000/A, 761Y30-11380000/A
    ACTIVE FILTERS: 24 V, AC/DC, On/Off service

## L5-05  (persona: typos-mixed)
Scripted user turns: ["Compara 761X30-11380000/A y 761Y30-11380000/A para apertura y cierre.", "¿Cuál ofrece más par y qué alimentación admite?"]

### Variant A
  > USER: Compara 761X30-11380000/A y 761Y30-11380000/A para apertura y cierre.   [3.42 s, HTTP 200]
    ANSWER: Comparing 761X30-11380000/A vs 761Y30-11380000/A. 6 identical fields hidden. | On/Off torque: 620 in-lb / 70 Nm vs 700 in-lb / 80 Nm | On/Off cycles: 350 /h vs 300 /h | Operating time (frequency not specified in the source): 17 s vs 20 s | FLA (frequency not specified in the source): 5 A vs 6.3 A
    COMPARISON: models=['761X30-11380000/A', '761Y30-11380000/A'] summary=761X30-11380000/A wins 3 of 4 differing fields with an agreed direction; 761Y30-11380000/A wins 1. This is an unweighted field count, not an overall suitability rating.
  > USER: ¿Cuál ofrece más par y qué alimentación admite?   [0.08 s, HTTP 200]
    ANSWER: 761Y30-11380000/A has the highest torque: 761X30-11380000/A 70 Nm vs 761Y30-11380000/A 80 Nm.
    PRODUCT CARD: 761Y30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=700; on_off_torque_nm=80; on_off_duty_s4_percent=30; cycles_per_hour=300; motor_power_w=40; operating_time_unqualified_s=20; fla_unqualified_a=6.3; lra_unqualified_a=12.8

## L6-01  (persona: out-of-scope)
Scripted user turns: ["Give the on/off torque of 762A00-11300000/A and a delivered price for ten units."]

### Variant A
  > USER: Give the on/off torque of 762A00-11300000/A and a delivered price for ten units.   [0.07 s, HTTP 200]
    ANSWER: The catalogue doesn't publish prices. A weighted price score is unavailable. | 762A00-11300000/A |  • On/Off torque: 1330 in-lb / 150 Nm |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150

## L6-02  (persona: out-of-scope)
Scripted user turns: ["Tell me the motor wattage of 761A00-11300000/A, then provide its wiring diagram and terminal numbers."]

### Variant A
  > USER: Tell me the motor wattage of 761A00-11300000/A, then provide its wiring diagram and terminal numbers.   [0.06 s, HTTP 200]
    ANSWER: The catalogue doesn't publish wiring diagram for 761A00-11300000/A. I can compare its published electrical fields.

## L6-03  (persona: out-of-scope)
Scripted user turns: ["For 761B00-11320000/A, give the 50 Hz travel time and tell me whether you can dispatch it tomorrow."]

### Variant A
  > USER: For 761B00-11320000/A, give the 50 Hz travel time and tell me whether you can dispatch it tomorrow.   [0.08 s, HTTP 200]
    ANSWER: The catalogue does not publish delivery times or lead times. | 761B00-11320000/A |  • Operating time at 50 Hz: 23 s |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 761B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | operating_time_50hz_s=23

## L6-04  (persona: out-of-scope)
Scripted user turns: ["Please quote a pneumatic replacement and also explain which electric supply types Series 76 lists."]

### Variant A
  > USER: Please quote a pneumatic replacement and also explain which electric supply types Series 76 lists.   [0.06 s, HTTP 200]
    ANSWER: 24 V AC/DC, 24 V DC, 110 V AC 1-phase, 220 V AC 1-phase, 220 V AC 3-phase

## L7-01  (persona: behavior)
Scripted user turns: ["Show weatherproof 220 V on/off units meeting at least 150 Nm.", "Among those displayed, recommend the quickest at 50 Hz.", "What torque and time support that choice?"]

### Variant A
  > USER: Show weatherproof 220 V on/off units meeting at least 150 Nm.   [2.12 s, HTTP 200]
    ANSWER: 21 actuators meet: Weatherproof, On/Off service, 220 V, torque >= 150 Nm. To narrow it down: number of phases. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762A00-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 1 A | 762B00-11320000/A: On/Off torque 200 Nm; FLA 50 Hz 1.1 A | 763A00-11330C00/A: Shared torque 300 Nm (same torque for On/Off and Modulating); FLA 50 Hz 1 A
    QUESTION CARD: How many phases? 1 phase(14)/3 phase(7)
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=21 shown: 762A00-11320000/A, 762B00-11320000/A, 763A00-11330C00/A
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200
    PRODUCT CARD: 763A00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=2650; shared_torque_nm=300
    CHIPS: Compare top 2 | Show all 21
    ACTIVE FILTERS: Weatherproof, On/Off service, 220 V, torque >= 150 Nm
  > USER: Among those displayed, recommend the quickest at 50 Hz.   [0.09 s, HTTP 200]
    ANSWER: I recommend 762A00-11320000/A: Operating time at 50 Hz 21 s; meets Weatherproof, On/Off service, 220 V, 50 Hz, torque >= 150 Nm. Ranked by fastest operating time, then lowest FLA, then part number. Versus 762B00-11320000/A: Operating time at 50 Hz: 21 s vs 29 s; FLA at 50 Hz: 1 A vs 1.1 A; On/Off cycles: 30 /h vs 21 /h. Choose 762B00-11320000/A only if its On/Off torque advantage (1750 in-lb / 200 Nm vs 1330 in-lb / 150 Nm) matters more than the stated priority. Assumes no preference on phase count; tell me if that matters.
    RANKED LIST: fastest operating time, then lowest FLA, then part number total=3 shown: 762A00-11320000/A, 762B00-11320000/A, 763A00-11330C00/A
    ACTIVE FILTERS: Weatherproof, 220 V, On/Off service, 50 Hz, torque >= 150 Nm
  > USER: What torque and time support that choice?   [4.11 s, HTTP 200]
    ANSWER: 762A00-11320000/A |  • On/Off torque: 1330 in-lb / 150 Nm |  • Operating time at 50 Hz: 21 s |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150; operating_time_50hz_s=21
    ACTIVE FILTERS: On/Off service, Weatherproof, 50 Hz, torque >= 150 Nm, 220 V

## L7-02  (persona: behavior)
Scripted user turns: ["List the 24 V models that accept both AC and DC.", "Compare the first two in that list.", "Choose between those two for an on/off valve needing 70 Nm."]

### Variant A
  > USER: List the 24 V models that accept both AC and DC.   [2.01 s, HTTP 200]
    ANSWER: 5 actuators meet: AC/DC, 24 V. Here are the leading published models. | Ranked by lowest FLA, then shortest operating time. | 761X30-11380000/A: Explosionproof; On/Off torque 70 Nm; FLA 5 A | 762X30-11380000/A: Explosionproof; On/Off torque 150 Nm; FLA 6 A | 761Y30-11380000/A: Explosionproof; On/Off torque 80 Nm; FLA 6.3 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    RANKED LIST: lowest FLA, then shortest operating time total=5 shown: 761X30-11380000/A, 762X30-11380000/A, 761Y30-11380000/A
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 761Y30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    CHIPS: Compare top 2 | Show all 5
    ACTIVE FILTERS: AC/DC, 24 V
  > USER: Compare the first two in that list.   [2.18 s, HTTP 200]
    ANSWER: Comparing 761X30-11380000/A vs 762X30-11380000/A. 4 identical fields hidden. | On/Off torque: 620 in-lb / 70 Nm vs 1350 in-lb / 150 Nm | On/Off duty S4: 30 % vs 40 % | On/Off cycles: 350 /h vs 200 /h | Operating time (frequency not specified in the source): 17 s vs 22 s | FLA (frequency not specified in the source): 5 A vs 6 A | LRA (frequency not specified in the source): 12.8 A vs 16.9 A
    COMPARISON: models=['761X30-11380000/A', '762X30-11380000/A'] summary=761X30-11380000/A wins 4 of 5 differing fields with an agreed direction; 762X30-11380000/A wins 1. This is an unweighted field count, not an overall suitability rating.
    ACTIVE FILTERS: AC/DC, 24 V
  > USER: Choose between those two for an on/off valve needing 70 Nm.   [5.39 s, HTTP 200]
    ANSWER: I recommend 761X30-11380000/A: Explosionproof; lowest torque 70 Nm; meets AC/DC, On/Off service, 24 V, torque ≥ 70 Nm. Ranked by lowest torque, then lowest FLA, then shortest operating time, then part number. Versus 762X30-11380000/A: FLA (frequency not specified in the source): 5 A vs 6 A; Operating time (frequency not specified in the source): 17 s vs 22 s; On/Off cycles: 350 /h vs 200 /h. Choose 762X30-11380000/A only if its On/Off torque advantage (1350 in-lb / 150 Nm vs 620 in-lb / 70 Nm) matters more than the stated priority. | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    RANKED LIST: lowest torque, then lowest FLA, then shortest operating time, then part number total=2 shown: 761X30-11380000/A, 762X30-11380000/A
    ACTIVE FILTERS: 24 V, AC/DC, On/Off service, torque ≥ 70 Nm

## L7-03  (persona: behavior)
Scripted user turns: ["I want the shortest travel time at 50 Hz, with 110 V weatherproof housing.", "The valve needs 150 Nm for on/off operation.", "Which displayed model best meets the objective I gave first?"]

### Variant A
  > USER: I want the shortest travel time at 50 Hz, with 110 V weatherproof housing.   [1.96 s, HTTP 200]
    ANSWER: 11 actuators meet: Weatherproof, 110 V, 50 Hz. Here are the leading published models. | Ranked by lowest FLA, then shortest operating time. | 761A00-11300000/A: On/Off torque 80 Nm; Modulating torque 65 Nm; FLA 50 Hz 1.1 A | 761B00-11300000/A: On/Off torque 100 Nm; Modulating torque 70 Nm; FLA 50 Hz 1.2 A | 762A00-11300000/A: On/Off torque 150 Nm; Modulating torque 130 Nm; FLA 50 Hz 2.3 A
    RANKED LIST: lowest FLA, then shortest operating time total=11 shown: 761A00-11300000/A, 761B00-11300000/A, 762A00-11300000/A
    PRODUCT CARD: 761A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80; modulating_torque_in_lb=580; modulating_torque_nm=65
    PRODUCT CARD: 761B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100; modulating_torque_in_lb=620; modulating_torque_nm=70
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150; modulating_torque_in_lb=1150; modulating_torque_nm=130
    CHIPS: Compare top 2 | Show all 11
    ACTIVE FILTERS: Weatherproof, 110 V, 50 Hz
  > USER: The valve needs 150 Nm for on/off operation.   [3.85 s, HTTP 200]
    ANSWER: 9 actuators meet: Weatherproof, On/Off service, 110 V, 50 Hz, torque >= 150 Nm. Here are the leading published models. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762A00-11300000/A: On/Off torque 150 Nm; FLA 50 Hz 2.3 A | 762B00-11300000/A: On/Off torque 200 Nm; FLA 50 Hz 2.3 A | 763A00-11300000/A: On/Off torque 300 Nm; FLA 50 Hz 2.5 A
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=9 shown: 762A00-11300000/A, 762B00-11300000/A, 763A00-11300000/A
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200
    PRODUCT CARD: 763A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=2650; on_off_torque_nm=300
    CHIPS: Compare top 2 | Show all 9
    ACTIVE FILTERS: Weatherproof, 50 Hz, 110 V, On/Off service, torque >= 150 Nm
  > USER: Which displayed model best meets the objective I gave first?   [0.1 s, HTTP 200]
    ANSWER: I recommend 762A00-11300000/A: On/Off torque 150 Nm; meets Weatherproof, On/Off service, 110 V, 50 Hz, torque >= 150 Nm. Ranked by closest torque at or above 150 Nm, then lowest FLA, then shortest operating time, then part number. Versus 762B00-11300000/A: Operating time at 50 Hz: 21 s vs 30 s; On/Off cycles: 42 /h vs 21 /h. Choose 762B00-11300000/A only if its On/Off torque advantage (1750 in-lb / 200 Nm vs 1330 in-lb / 150 Nm) matters more than the stated priority.
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA, then shortest operating time, then part number total=3 shown: 762A00-11300000/A, 762B00-11300000/A, 763A00-11300000/A
    ACTIVE FILTERS: Weatherproof, 110 V, On/Off service, 50 Hz, torque >= 150 Nm

## L7-04  (persona: behavior)
Scripted user turns: ["This will operate a valve in a room with flammable solvent vapour. Supply is 220 V and the valve needs 150 Nm on/off.", "Can you show explosionproof candidates?", "Does a catalogue entry alone establish that it is safe for my exact site?"]

### Variant A
  > USER: This will operate a valve in a room with flammable solvent vapour. Supply is 220 V and the valve needs 150 Nm on/off.   [2.24 s, HTTP 200]
    ANSWER: 8 actuators meet: Explosionproof, On/Off service, 220 V, torque >= 150 Nm. Here are the leading published models. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762X30-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 0.9 A | 762Y30-11320000/A: On/Off torque 180 Nm; FLA 50 Hz 1 A | 763X30-11320000/A: On/Off torque 260 Nm; FLA 50 Hz 1.3 A
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=8 shown: 762X30-11320000/A, 762Y30-11320000/A, 763X30-11320000/A
    PRODUCT CARD: 762X30-11320000/A | explosionproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 762Y30-11320000/A | explosionproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1590; on_off_torque_nm=180
    PRODUCT CARD: 763X30-11320000/A | explosionproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=2300; on_off_torque_nm=260
    CHIPS: Compare top 2 | Show all 8
    ACTIVE FILTERS: Explosionproof, On/Off service, 220 V, torque >= 150 Nm
  > USER: Can you show explosionproof candidates?   [3.18 s, HTTP 200]
    ANSWER: 8 actuators meet: Explosionproof, On/Off service, 220 V, torque >= 150 Nm. Here are the leading published models. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762X30-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 0.9 A | 762Y30-11320000/A: On/Off torque 180 Nm; FLA 50 Hz 1 A | 763X30-11320000/A: On/Off torque 260 Nm; FLA 50 Hz 1.3 A
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=8 shown: 762X30-11320000/A, 762Y30-11320000/A, 763X30-11320000/A
    PRODUCT CARD: 762X30-11320000/A | explosionproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 762Y30-11320000/A | explosionproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1590; on_off_torque_nm=180
    PRODUCT CARD: 763X30-11320000/A | explosionproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=2300; on_off_torque_nm=260
    CHIPS: Compare top 2 | Show all 8
    ACTIVE FILTERS: On/Off service, Explosionproof, torque >= 150 Nm, 220 V
  > USER: Does a catalogue entry alone establish that it is safe for my exact site?   [1.66 s, HTTP 200]
    ANSWER: N/A means the source does not provide an available value for that field. It is not zero and cannot be inferred from another model.
    ACTIVE FILTERS: On/Off service, Explosionproof, torque >= 150 Nm, 220 V

## L7-05  (persona: behavior)
Scripted user turns: ["The site is a non-hazardous outdoor irrigation station, 110 V, open/close, 80 Nm.", "Show the weatherproof choices.", "Of the ones shown, which has the shortest 50 Hz travel time?"]

### Variant A
  > USER: The site is a non-hazardous outdoor irrigation station, 110 V, open/close, 80 Nm.   [2.29 s, HTTP 200]
    ANSWER: 11 actuators meet: Weatherproof, On/Off service, 110 V, torque ≥ 80 Nm. Here are the leading published models. | Interpretation: 'outdoor' read as Weatherproof; 'open/close' read as On/Off service. | Ranked by closest torque at or above 80 Nm, then lowest FLA. | 761A00-11300000/A: On/Off torque 80 Nm; FLA 50 Hz 1.1 A | 761B00-11300000/A: On/Off torque 100 Nm; FLA 50 Hz 1.2 A | 762A00-11300000/A: On/Off torque 150 Nm; FLA 50 Hz 2.3 A
    RANKED LIST: closest torque at or above 80 Nm, then lowest FLA total=11 shown: 761A00-11300000/A, 761B00-11300000/A, 762A00-11300000/A
    PRODUCT CARD: 761A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    PRODUCT CARD: 761B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    CHIPS: Compare top 2 | Show all 11
    ACTIVE FILTERS: Weatherproof, On/Off service, 110 V, torque ≥ 80 Nm
  > USER: Show the weatherproof choices.   [3.34 s, HTTP 200]
    ANSWER: 11 actuators meet: Weatherproof, On/Off service, 110 V, torque ≥ 80 Nm. Here are the leading published models. | Ranked by closest torque at or above 80 Nm, then lowest FLA. | 761A00-11300000/A: On/Off torque 80 Nm; FLA 50 Hz 1.1 A | 761B00-11300000/A: On/Off torque 100 Nm; FLA 50 Hz 1.2 A | 762A00-11300000/A: On/Off torque 150 Nm; FLA 50 Hz 2.3 A
    RANKED LIST: closest torque at or above 80 Nm, then lowest FLA total=11 shown: 761A00-11300000/A, 761B00-11300000/A, 762A00-11300000/A
    PRODUCT CARD: 761A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    PRODUCT CARD: 761B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    CHIPS: Compare top 2 | Show all 11
    ACTIVE FILTERS: On/Off service, Weatherproof, torque ≥ 80 Nm, 110 V
  > USER: Of the ones shown, which has the shortest 50 Hz travel time?   [0.13 s, HTTP 200]
    ANSWER: 761A00-11300000/A has the lowest operating time at 50 Hz: 20 s at 50 Hz.
    PRODUCT CARD: 761A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80; on_off_duty_s4_percent=40; modulating_torque_in_lb=580; modulating_torque_nm=65; modulating_duty_s4_percent=40; cycles_per_hour=36; starts_per_hour=960; motor_power_w=15; operating_time_60hz_s=17
    ACTIVE FILTERS: On/Off service, Weatherproof, torque ≥ 80 Nm, 110 V

## L7-06  (persona: behavior)
Scripted user turns: ["For 761A00-11330C00/A, what is the operating time?", "Could you use the corresponding single-phase model's value instead?", "If not, leave the unavailable figure explicit."]

### Variant A
  > USER: For 761A00-11330C00/A, what is the operating time?   [1.86 s, HTTP 200]
    ANSWER: 761A00-11330C00/A | 761A00-11330C00/A — Weatherproof, 220 V AC 3-phase: every performance value of this row is N/A in the source table; nothing can be inferred.
    PRODUCT CARD: 761A00-11330C00/A | weatherproof | 220 V AC | 3-phase | source_NA | 
  > USER: Could you use the corresponding single-phase model's value instead?   [6.43 s, HTTP 200]
    ANSWER: 761A00-11330C00/A | 761A00-11330C00/A — Weatherproof, 220 V AC 3-phase: every performance value of this row is N/A in the source table; nothing can be inferred.
    PRODUCT CARD: 761A00-11330C00/A | weatherproof | 220 V AC | 3-phase | source_NA | 
  > USER: If not, leave the unavailable figure explicit.   [1.88 s, HTTP 200]
    ANSWER: 761A00-11330C00/A | 761A00-11330C00/A — Weatherproof, 220 V AC 3-phase: every performance value of this row is N/A in the source table; nothing can be inferred.
    PRODUCT CARD: 761A00-11330C00/A | weatherproof | 220 V AC | 3-phase | source_NA | 

## L7-07  (persona: behavior)
Scripted user turns: ["Give me a quick overview of 762A00-11300000/A.", "What changes if I use it for modulation rather than just opening and closing?"]

### Variant A
  > USER: Give me a quick overview of 762A00-11300000/A.   [0.07 s, HTTP 200]
    ANSWER: That isn't published in the Series 76 catalogue. I can show its published specifications.
  > USER: What changes if I use it for modulation rather than just opening and closing?   [7.05 s, HTTP 200]
    ANSWER: 762A00-11300000/A |  • On/Off torque: 1330 in-lb / 150 Nm |  • Modulating torque: 1150 in-lb / 130 Nm |  • Duty S4 On/Off: 50% |  • Duty S4 Modulating: 40% |  • On/Off cycles per hour: 42 |  • Modulating starts per hour: 960 |  • Operating time at 50 Hz: 21 s |  • Operating time at 60 Hz: 18 s |  • FLA at 50 Hz: 2.3 A |  • FLA at 60 Hz: 2.3 A |  • LRA at 50 Hz: 2.4 A |  • LRA at 60 Hz: 2.5 A |  • Motor power: 40 W |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150; on_off_duty_s4_percent=50; modulating_torque_in_lb=1150; modulating_torque_nm=130; modulating_duty_s4_percent=40; cycles_per_hour=42; starts_per_hour=960; motor_power_w=40; operating_time_60hz_s=18

## L7-08  (persona: behavior)
Scripted user turns: ["Find a weatherproof 24 V DC-only unit with 100000 Nm of torque.", "Don't loosen any of those requirements.", "Explain whether the catalogue contains an exact match."]

### Variant A
  > USER: Find a weatherproof 24 V DC-only unit with 100000 Nm of torque.   [6.17 s, HTTP 200]
    ANSWER: No actuator meets Weatherproof, DC, DC-only models, 24 V, torque >= 100000 Nm. | DC-only eligibility excludes AC/DC models.
    ACTIVE FILTERS: Weatherproof, DC, DC-only models, 24 V, torque >= 100000 Nm
  > USER: Don't loosen any of those requirements.   [3.26 s, HTTP 200]
    ANSWER: No problem. Share any requirements whenever you like, or ask about a specific part number. | DC-only eligibility excludes AC/DC models.
    ACTIVE FILTERS: DC-only models, Weatherproof, torque >= 100000 Nm, DC, 24 V
  > USER: Explain whether the catalogue contains an exact match.   [1.94 s, HTTP 200]
    ANSWER: No actuator meets Weatherproof, DC, DC-only models, 24 V, torque >= 100000 Nm. | DC-only eligibility excludes AC/DC models.
    ACTIVE FILTERS: DC-only models, Weatherproof, torque >= 100000 Nm, DC, 24 V

## L7-09  (persona: behavior)
Scripted user turns: ["Show the on/off torque and enclosure for 761Y30-11380000/A.", "Would it accept DC power?", "Does accepting DC mean it is a DC-only model?"]

### Variant A
  > USER: Show the on/off torque and enclosure for 761Y30-11380000/A.   [0.07 s, HTTP 200]
    ANSWER: Published enclosures: Explosionproof (30 models), Weatherproof (34 models).
  > USER: Would it accept DC power?   [2.34 s, HTTP 200]
    ANSWER: Which shown model do you mean?
  > USER: Does accepting DC mean it is a DC-only model?   [5.53 s, HTTP 200]
    ANSWER: 24 V AC/DC, 24 V DC, 110 V AC 1-phase, 220 V AC 1-phase, 220 V AC 3-phase