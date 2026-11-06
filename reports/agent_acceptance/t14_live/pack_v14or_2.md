
## L3-01  (persona: impatient)
Scripted user turns: ["762B00-11300000/A. Motor watts. Keep it short."]

### Variant A
  > USER: 762B00-11300000/A. Motor watts. Keep it short.   [2.7 s, HTTP 200]
    ANSWER: 762B00-11300000/A |  • Motor power: 40 W |  Source: Series 76 electrical catalogue, page 1. | Motor power is the rated power of the internal motor; the catalogue does not publish total electrical consumption.
    PRODUCT CARD: 762B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | motor_power_w=40

## L3-02  (persona: impatient)
Scripted user turns: ["220 V. Weatherproof. Open/close.", "150 Nm minimum.", "List them."]

### Variant A
  > USER: 220 V. Weatherproof. Open/close.   [3.51 s, HTTP 200]
    ANSWER: 23 actuators meet: Weatherproof, On/Off service, 220 V. To narrow it down: number of phases. | Interpretation: 'Open/close' read as On/Off service. | Ranked by lowest FLA, then shortest operating time. | 761A00-11320000/A: On/Off torque 80 Nm; FLA 50 Hz 0.7 A | 761B00-11320000/A: On/Off torque 100 Nm; FLA 50 Hz 0.7 A | 762A00-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 1 A
    QUESTION CARD: How many phases? 1 phase(16)/3 phase(7)
    RANKED LIST: lowest FLA, then shortest operating time total=23 shown: 761A00-11320000/A, 761B00-11320000/A, 762A00-11320000/A
    PRODUCT CARD: 761A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    PRODUCT CARD: 761B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    CHIPS: Compare top 2 | Show all 23
    ACTIVE FILTERS: Weatherproof, On/Off service, 220 V
  > USER: 150 Nm minimum.   [2.11 s, HTTP 200]
    ANSWER: 21 actuators meet: Weatherproof, On/Off service, 220 V, torque >= 150 Nm. To narrow it down: number of phases. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762A00-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 1 A | 762B00-11320000/A: On/Off torque 200 Nm; FLA 50 Hz 1.1 A | 763A00-11330C00/A: Shared torque 300 Nm (same torque for On/Off and Modulating); FLA 50 Hz 1 A
    QUESTION CARD: How many phases? 1 phase(14)/3 phase(7)
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=21 shown: 762A00-11320000/A, 762B00-11320000/A, 763A00-11330C00/A
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200
    PRODUCT CARD: 763A00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=2650; shared_torque_nm=300
    CHIPS: Compare top 2 | Show all 21
    ACTIVE FILTERS: On/Off service, Weatherproof, 220 V, torque >= 150 Nm
  > USER: List them.   [2.6 s, HTTP 200]
    ANSWER: 21 ranked models. Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762A00-11320000/A | 762B00-11320000/A | 763A00-11330C00/A | 763A00-11320000/A | 763B00-11330C00/A | 763B00-11320000/A | 763C00-11320000/A | 763C00-11330C00/A | 764A00-11320000/A | 764A00-11330C00/A | 764B00-11320000/A | 764B00-11330C00/A | 765A00-11320000/A | 765A00-11330C00/A | 765B00-11330C00/A | 765B00-11320000/A | 766A00-11320000/A | 766B00-11320000/A | 767A00-11320000/A | 767B00-11320000/A | 767C00-11320000/A
    ACTIVE FILTERS: On/Off service, Weatherproof, torque >= 150 Nm, 220 V

## L3-03  (persona: impatient)
Scripted user turns: ["24 V AC/DC. Explosionproof.", "Show choices.", "Recommend one from that list for 70 Nm on/off."]

### Variant A
  > USER: 24 V AC/DC. Explosionproof.   [3.11 s, HTTP 200]
    ANSWER: 5 actuators meet: Explosionproof, AC/DC, 24 V. Here are the leading published models. | Ranked by lowest FLA, then shortest operating time. | 761X30-11380000/A: On/Off torque 70 Nm; FLA 5 A | 762X30-11380000/A: On/Off torque 150 Nm; FLA 6 A | 761Y30-11380000/A: On/Off torque 80 Nm; FLA 6.3 A
    RANKED LIST: lowest FLA, then shortest operating time total=5 shown: 761X30-11380000/A, 762X30-11380000/A, 761Y30-11380000/A
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 761Y30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    CHIPS: Compare top 2 | Show all 5
    ACTIVE FILTERS: Explosionproof, 24 V, AC/DC
  > USER: Show choices.   [1.77 s, HTTP 200]
    ANSWER: 5 ranked models. Ranked by lowest FLA, then shortest operating time. | 761X30-11380000/A | 762X30-11380000/A | 761Y30-11380000/A | 762Y30-11380000/A | 763X30-11380000/A
    ACTIVE FILTERS: Explosionproof, AC/DC, 24 V
  > USER: Recommend one from that list for 70 Nm on/off.   [0.1 s, HTTP 200]
    ANSWER: I recommend 761X30-11380000/A: On/Off torque 70 Nm; meets Explosionproof, AC/DC, On/Off service, 24 V, torque ≥ 70 Nm. Ranked by closest torque at or above 70 Nm, then lowest FLA, then shortest operating time, then part number. Versus 761Y30-11380000/A: FLA (frequency not specified in the source): 5 A vs 6.3 A; Operating time (frequency not specified in the source): 17 s vs 20 s; On/Off cycles: 350 /h vs 300 /h. Choose 761Y30-11380000/A only if its On/Off torque advantage (700 in-lb / 80 Nm vs 620 in-lb / 70 Nm) matters more than the stated priority.
    RANKED LIST: closest torque at or above 70 Nm, then lowest FLA, then shortest operating time, then part number total=3 shown: 761X30-11380000/A, 761Y30-11380000/A, 762X30-11380000/A
    ACTIVE FILTERS: Explosionproof, 24 V, AC/DC, On/Off service, torque ≥ 70 Nm

## L3-04  (persona: impatient)
Scripted user turns: ["761A00-11320000/A cycles per hour?"]

### Variant A
  > USER: 761A00-11320000/A cycles per hour?   [3.0 s, HTTP 200]
    ANSWER: 761A00-11320000/A |  • On/Off cycles per hour: 36 |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 761A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | cycles_per_hour=36

## L3-05  (persona: impatient)
Scripted user turns: ["Need 90000 Nm, 24 V, open/close. Exact match only."]

### Variant A
  > USER: Need 90000 Nm, 24 V, open/close. Exact match only.   [9.32 s, HTTP 200]
    ANSWER: No actuator in the supplied catalogue meets all of: On/Off service, 24 V, torque >= 90000 Nm. | Closest published On/Off torque: 240 Nm, held by 763X30-11380000/A. | 763X30-11380000/A: Does not meet torque >= 90000 Nm; closest published value in this scope is 240. | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    RANKED LIST: Alternatives after relaxing a requirement total=0 shown: 
    CHIPS: Show 763X30-11380000/A | Find actuators with On/Off service, 24 V, torque >= 240 Nm
    ACTIVE FILTERS: On/Off service, 24 V, torque >= 90000 Nm

## L3-06  (persona: impatient)
Scripted user turns: ["Compare the first two you showed.", "I haven't given you any models yet. What do you need?"]

### Variant A
  > USER: Compare the first two you showed.   [5.43 s, HTTP 200]
    ANSWER: Which shown model do you mean?
  > USER: I haven't given you any models yet. What do you need?   [4.69 s, HTTP 200]
    ANSWER: Tell me what it must do: open/close or modulate, supply voltage, and the torque you need.
    QUESTION CARD: Which supply voltage? 24 V(10)/110 V(21)/220 V(33); Which enclosure? Explosionproof(30)/Weatherproof(34)

## L4-01  (persona: mind-changer)
Scripted user turns: ["Find explosionproof 24 V DC-compatible units for on/off operation.", "Correction: DC only, not the dual-supply ones.", "Remove the DC-only restriction; AC/DC units are acceptable again."]

### Variant A
  > USER: Find explosionproof 24 V DC-compatible units for on/off operation.   [2.23 s, HTTP 200]
    ANSWER: 5 actuators meet: Explosionproof, DC, On/Off service, 24 V. To narrow it down: minimum torque. | Ranked by lowest FLA, then shortest operating time. | 761X30-11380000/A: On/Off torque 70 Nm; FLA 5 A | 762X30-11380000/A: On/Off torque 150 Nm; FLA 6 A | 761Y30-11380000/A: On/Off torque 80 Nm; FLA 6.3 A | For a DC supply, compatible AC/DC models remain eligible.
    QUESTION CARD: What minimum torque do you need? 80 Nm or more(4)/150 Nm or more(3)/160 Nm or more(2)
    RANKED LIST: lowest FLA, then shortest operating time total=5 shown: 761X30-11380000/A, 762X30-11380000/A, 761Y30-11380000/A
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 761Y30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    CHIPS: Compare top 2 | Show all 5
    ACTIVE FILTERS: Explosionproof, DC, On/Off service, 24 V
  > USER: Correction: DC only, not the dual-supply ones.   [3.85 s, HTTP 200]
    ANSWER: No actuator meets Explosionproof, DC, On/Off service, DC-only models, 24 V. | DC-only eligibility excludes AC/DC models.
    ACTIVE FILTERS: On/Off service, Explosionproof, DC, 24 V, DC-only models
  > USER: Remove the DC-only restriction; AC/DC units are acceptable again.   [3.84 s, HTTP 200]
    ANSWER: 5 actuators meet: Explosionproof, DC, On/Off service, 24 V. To narrow it down: minimum torque. | Ranked by lowest FLA, then shortest operating time. | 761X30-11380000/A: On/Off torque 70 Nm; FLA 5 A | 762X30-11380000/A: On/Off torque 150 Nm; FLA 6 A | 761Y30-11380000/A: On/Off torque 80 Nm; FLA 6.3 A | For a DC supply, compatible AC/DC models remain eligible.
    QUESTION CARD: What minimum torque do you need? 80 Nm or more(4)/150 Nm or more(3)/160 Nm or more(2)
    RANKED LIST: lowest FLA, then shortest operating time total=5 shown: 761X30-11380000/A, 762X30-11380000/A, 761Y30-11380000/A
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 761Y30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    CHIPS: Compare top 2 | Show all 5
    ACTIVE FILTERS: On/Off service, Explosionproof, DC, 24 V

## L4-02  (persona: mind-changer)
Scripted user turns: ["I need a weatherproof 110 V actuator for opening and closing, at least 150 Nm.", "I wrote the wrong voltage: the panel is 220 V.", "Keep the torque and enclosure requirements."]

### Variant A
  > USER: I need a weatherproof 110 V actuator for opening and closing, at least 150 Nm.   [2.32 s, HTTP 200]
    ANSWER: 9 actuators meet: Weatherproof, On/Off service, 110 V, torque >= 150 Nm. Here are the leading published models. | Interpretation: 'opening and closing' read as On/Off service. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762A00-11300000/A: On/Off torque 150 Nm; FLA 50 Hz 2.3 A | 762B00-11300000/A: On/Off torque 200 Nm; FLA 50 Hz 2.3 A | 763A00-11300000/A: On/Off torque 300 Nm; FLA 50 Hz 2.5 A
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=9 shown: 762A00-11300000/A, 762B00-11300000/A, 763A00-11300000/A
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200
    PRODUCT CARD: 763A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=2650; on_off_torque_nm=300
    CHIPS: Compare top 2 | Show all 9
    ACTIVE FILTERS: Weatherproof, On/Off service, 110 V, torque >= 150 Nm
  > USER: I wrote the wrong voltage: the panel is 220 V.   [2.55 s, HTTP 200]
    ANSWER: 21 actuators meet: Weatherproof, On/Off service, 220 V, torque >= 150 Nm. To narrow it down: number of phases. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762A00-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 1 A | 762B00-11320000/A: On/Off torque 200 Nm; FLA 50 Hz 1.1 A | 763A00-11330C00/A: Shared torque 300 Nm (same torque for On/Off and Modulating); FLA 50 Hz 1 A
    QUESTION CARD: How many phases? 1 phase(14)/3 phase(7)
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=21 shown: 762A00-11320000/A, 762B00-11320000/A, 763A00-11330C00/A
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200
    PRODUCT CARD: 763A00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=2650; shared_torque_nm=300
    CHIPS: Compare top 2 | Show all 21
    ACTIVE FILTERS: On/Off service, Weatherproof, torque >= 150 Nm, 220 V
  > USER: Keep the torque and enclosure requirements.   [5.41 s, HTTP 200]
    ANSWER: These are the best matches so far. You can narrow them by phase count: | 762A00-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 1 A | 762B00-11320000/A: On/Off torque 200 Nm; FLA 50 Hz 1.1 A | 763A00-11330C00/A: Shared torque 300 Nm (same torque for On/Off and Modulating); FLA 50 Hz 1 A
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150; on_off_duty_s4_percent=35; modulating_torque_in_lb=1150; modulating_torque_nm=130; modulating_duty_s4_percent=40; cycles_per_hour=30; starts_per_hour=960; motor_power_w=40; operating_time_60hz_s=18
    PRODUCT CARD: 762B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200; on_off_duty_s4_percent=35; modulating_torque_in_lb=1330; modulating_torque_nm=150; modulating_duty_s4_percent=40; cycles_per_hour=21; starts_per_hour=960; motor_power_w=40; operating_time_60hz_s=24
    PRODUCT CARD: 763A00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=2650; shared_torque_nm=300; shared_duty_s4_percent=70; cycles_per_hour=39; starts_per_hour=1200; motor_power_w=40; operating_time_60hz_s=26; fla_60hz_a=1; lra_60hz_a=1.2; operating_time_50hz_s=32
    ACTIVE FILTERS: On/Off service, Weatherproof, torque >= 150 Nm, 220 V

## L4-03  (persona: mind-changer)
Scripted user turns: ["Start with 220 V three-phase weatherproof choices.", "I no longer care about phase count.", "Make the service modulating instead of on/off."]

### Variant A
  > USER: Start with 220 V three-phase weatherproof choices.   [2.38 s, HTTP 200]
    ANSWER: 7 actuators meet: Weatherproof, 3-phase, 220 V. Here are the leading published models. | Ranked by lowest FLA, then shortest operating time. | 763A00-11330C00/A: Shared torque 300 Nm (same torque for On/Off and Modulating); FLA 50 Hz 1 A | 763B00-11330C00/A: Shared torque 500 Nm (same torque for On/Off and Modulating); FLA 50 Hz 2 A | 763C00-11330C00/A: Shared torque 600 Nm (same torque for On/Off and Modulating); FLA 50 Hz 2 A
    RANKED LIST: lowest FLA, then shortest operating time total=7 shown: 763A00-11330C00/A, 763B00-11330C00/A, 763C00-11330C00/A
    PRODUCT CARD: 763A00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=2650; shared_torque_nm=300
    PRODUCT CARD: 763B00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=4400; shared_torque_nm=500
    PRODUCT CARD: 763C00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=5300; shared_torque_nm=600
    CHIPS: Compare top 2 | Show all 7
    ACTIVE FILTERS: Weatherproof, 3-phase, 220 V
  > USER: I no longer care about phase count.   [2.61 s, HTTP 200]
    ANSWER: 23 actuators meet: Weatherproof, 220 V. Here are the leading published models. | Ranked by lowest FLA, then shortest operating time. | 761A00-11320000/A: On/Off torque 80 Nm; Modulating torque 65 Nm; FLA 50 Hz 0.7 A | 761B00-11320000/A: On/Off torque 100 Nm; Modulating torque 70 Nm; FLA 50 Hz 0.7 A | 762A00-11320000/A: On/Off torque 150 Nm; Modulating torque 130 Nm; FLA 50 Hz 1 A
    RANKED LIST: lowest FLA, then shortest operating time total=23 shown: 761A00-11320000/A, 761B00-11320000/A, 762A00-11320000/A
    PRODUCT CARD: 761A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80; modulating_torque_in_lb=580; modulating_torque_nm=65
    PRODUCT CARD: 761B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100; modulating_torque_in_lb=620; modulating_torque_nm=70
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150; modulating_torque_in_lb=1150; modulating_torque_nm=130
    CHIPS: Compare top 2 | Show all 23
    ACTIVE FILTERS: Weatherproof, 220 V
  > USER: Make the service modulating instead of on/off.   [2.28 s, HTTP 200]
    ANSWER: 23 actuators meet: Weatherproof, Modulating service, 220 V. To narrow it down: minimum torque. | Ranked by lowest FLA, then shortest operating time. | 761A00-11320000/A: Modulating torque 65 Nm; FLA 50 Hz 0.7 A | 761B00-11320000/A: Modulating torque 70 Nm; FLA 50 Hz 0.7 A | 762A00-11320000/A: Modulating torque 130 Nm; FLA 50 Hz 1 A
    QUESTION CARD: What minimum torque do you need? 300 Nm or more(18)/680 Nm or more(13)/3000 Nm or more(6)
    RANKED LIST: lowest FLA, then shortest operating time total=23 shown: 761A00-11320000/A, 761B00-11320000/A, 762A00-11320000/A
    PRODUCT CARD: 761A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | modulating_torque_in_lb=580; modulating_torque_nm=65
    PRODUCT CARD: 761B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | modulating_torque_in_lb=620; modulating_torque_nm=70
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | modulating_torque_in_lb=1150; modulating_torque_nm=130
    CHIPS: Compare top 2 | Show all 23
    ACTIVE FILTERS: Weatherproof, 220 V, Modulating service

## L4-04  (persona: mind-changer)
Scripted user turns: ["We need an explosionproof enclosure for a solvent mixing area, 24 V.", "The installation has moved to a non-hazardous water room; withdraw the explosionproof requirement.", "Keep 24 V and show what is available."]

### Variant A
  > USER: We need an explosionproof enclosure for a solvent mixing area, 24 V.   [2.05 s, HTTP 200]
    ANSWER: 10 actuators meet: Explosionproof, 24 V. To narrow it down: current type. | Interpretation: 'solvent mixing area' read as Explosionproof. | Ranked by lowest FLA, then shortest operating time. | 761X30-11370000/A: Modulating torque 65 Nm; FLA (DC) 5 A | 761X30-11380000/A: On/Off torque 70 Nm; FLA 5 A | 762X30-11370000/A: Modulating torque 130 Nm; FLA (DC) 6 A
    QUESTION CARD: Which current type? AC/DC(5)/DC(5)
    RANKED LIST: lowest FLA, then shortest operating time total=10 shown: 761X30-11370000/A, 761X30-11380000/A, 762X30-11370000/A
    PRODUCT CARD: 761X30-11370000/A | explosionproof | 24 V DC | reported | modulating_torque_in_lb=560; modulating_torque_nm=65
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11370000/A | explosionproof | 24 V DC | reported | modulating_torque_in_lb=1150; modulating_torque_nm=130
    CHIPS: Compare top 2 | Show all 10
    ACTIVE FILTERS: Explosionproof, 24 V
  > USER: The installation has moved to a non-hazardous water room; withdraw the explosionproof requirement.   [0.13 s, HTTP 200]
    ANSWER: 10 actuators meet: 24 V. To narrow it down: current type. | Ranked by lowest FLA, then shortest operating time. | 761X30-11370000/A: Explosionproof; Modulating torque 65 Nm; FLA (DC) 5 A | 761X30-11380000/A: Explosionproof; On/Off torque 70 Nm; FLA 5 A | 762X30-11370000/A: Explosionproof; Modulating torque 130 Nm; FLA (DC) 6 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    QUESTION CARD: Which current type? AC/DC(5)/DC(5)
    RANKED LIST: lowest FLA, then shortest operating time total=10 shown: 761X30-11370000/A, 761X30-11380000/A, 762X30-11370000/A
    PRODUCT CARD: 761X30-11370000/A | explosionproof | 24 V DC | reported | modulating_torque_in_lb=560; modulating_torque_nm=65
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11370000/A | explosionproof | 24 V DC | reported | modulating_torque_in_lb=1150; modulating_torque_nm=130
    CHIPS: Compare top 2 | Show all 10
    ACTIVE FILTERS: 24 V
  > USER: Keep 24 V and show what is available.   [2.11 s, HTTP 200]
    ANSWER: These are the best matches so far. You can narrow them by supply current: | 761X30-11370000/A: Modulating torque 65 Nm; FLA (DC) 5 A | 761X30-11380000/A: On/Off torque 70 Nm; FLA 5 A | 762X30-11370000/A: Modulating torque 130 Nm; FLA (DC) 6 A
    PRODUCT CARD: 761X30-11370000/A | explosionproof | 24 V DC | reported | modulating_torque_in_lb=560; modulating_torque_nm=65; modulating_duty_s4_percent=30; starts_per_hour=720; motor_power_w=40; operating_time_unqualified_s=17; fla_unqualified_a=5; lra_unqualified_a=12.8
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70; on_off_duty_s4_percent=30; cycles_per_hour=350; motor_power_w=40; operating_time_unqualified_s=17; fla_unqualified_a=5; lra_unqualified_a=12.8
    PRODUCT CARD: 762X30-11370000/A | explosionproof | 24 V DC | reported | modulating_torque_in_lb=1150; modulating_torque_nm=130; modulating_duty_s4_percent=40; starts_per_hour=960; motor_power_w=40; operating_time_unqualified_s=22; fla_unqualified_a=6; lra_unqualified_a=16.9
    ACTIVE FILTERS: 24 V

## L4-05  (persona: mind-changer)
Scripted user turns: ["Compare 761A00-11300000/A with 761B00-11300000/A for on/off use.", "I said fastest, but I actually want the higher torque of those two.", "Use 50 Hz when reporting the travel time."]

### Variant A
  > USER: Compare 761A00-11300000/A with 761B00-11300000/A for on/off use.   [2.38 s, HTTP 200]
    ANSWER: Comparing 761A00-11300000/A vs 761B00-11300000/A. 10 identical fields hidden. | On/Off torque: 700 in-lb / 80 Nm vs 880 in-lb / 100 Nm | Modulating torque: 580 in-lb / 65 Nm vs 620 in-lb / 70 Nm | On/Off cycles: 36 /h vs 31 /h | Operating time at 50 Hz: 20 s vs 23 s | FLA at 50 Hz: 1.1 A vs 1.2 A | Operating time at 60 Hz: 17 s vs 19 s | FLA at 60 Hz: 1.2 A vs 1.3 A
    COMPARISON: models=['761A00-11300000/A', '761B00-11300000/A'] summary=761A00-11300000/A wins 5 of 7 differing fields with an agreed direction; 761B00-11300000/A wins 2. This is an unweighted field count, not an overall suitability rating.
  > USER: I said fastest, but I actually want the higher torque of those two.   [0.08 s, HTTP 200]
    ANSWER: 761B00-11300000/A has the highest operating time: 761A00-11300000/A 17 s at 60 Hz vs 761B00-11300000/A 19 s at 60 Hz.
    PRODUCT CARD: 761B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100; on_off_duty_s4_percent=40; modulating_torque_in_lb=620; modulating_torque_nm=70; modulating_duty_s4_percent=40; cycles_per_hour=31; starts_per_hour=960; motor_power_w=15; operating_time_60hz_s=19
  > USER: Use 50 Hz when reporting the travel time.   [5.49 s, HTTP 200]
    ANSWER: 761B00-11300000/A |  • Operating time at 50 Hz: 23 s |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 761B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | operating_time_50hz_s=23

## L4-06  (persona: mind-changer)
Scripted user turns: ["Busco un equipo de 220 V para operación de apertura y cierre, mínimo 150 Nm.", "Corrijo: son 110 V; conserva el mínimo de par.", "Ya no exijo una carcasa a prueba de explosión."]

### Variant A
  > USER: Busco un equipo de 220 V para operación de apertura y cierre, mínimo 150 Nm.   [3.43 s, HTTP 200]
    ANSWER: 29 actuators meet: On/Off service, 220 V, torque >= 150 Nm. To narrow it down: enclosure and number of phases. | Interpretation: 'operación de apertura y cierre' read as On/Off service. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762X30-11320000/A: Explosionproof; On/Off torque 150 Nm; FLA 50 Hz 0.9 A | 762A00-11320000/A: Weatherproof; On/Off torque 150 Nm; FLA 50 Hz 1 A | 762Y30-11320000/A: Explosionproof; On/Off torque 180 Nm; FLA 50 Hz 1 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    QUESTION CARD: Which enclosure? Explosionproof(8)/Weatherproof(21); How many phases? 1 phase(22)/3 phase(7)
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=29 shown: 762X30-11320000/A, 762A00-11320000/A, 762Y30-11320000/A
    PRODUCT CARD: 762X30-11320000/A | explosionproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762Y30-11320000/A | explosionproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1590; on_off_torque_nm=180
    CHIPS: Compare top 2 | Show all 29
    ACTIVE FILTERS: On/Off service, 220 V, torque >= 150 Nm
  > USER: Corrijo: son 110 V; conserva el mínimo de par.   [4.11 s, HTTP 200]
    ANSWER: 17 actuators meet: On/Off service, 110 V, torque >= 150 Nm. To narrow it down: enclosure. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762X30-11300000/A: Explosionproof; On/Off torque 150 Nm; FLA 50 Hz 1.9 A | 762A00-11300000/A: Weatherproof; On/Off torque 150 Nm; FLA 50 Hz 2.3 A | 762Y30-11300000/A: Explosionproof; On/Off torque 200 Nm; FLA 50 Hz 2.2 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    QUESTION CARD: Which enclosure? Explosionproof(8)/Weatherproof(9)
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=17 shown: 762X30-11300000/A, 762A00-11300000/A, 762Y30-11300000/A
    PRODUCT CARD: 762X30-11300000/A | explosionproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762Y30-11300000/A | explosionproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1770; on_off_torque_nm=200
    CHIPS: Compare top 2 | Show all 17
    ACTIVE FILTERS: On/Off service, torque >= 150 Nm, 110 V
  > USER: Ya no exijo una carcasa a prueba de explosión.   [0.12 s, HTTP 200]
    ANSWER: 17 actuators meet: On/Off service, 110 V, torque >= 150 Nm. Here are the leading published models. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762X30-11300000/A: Explosionproof; On/Off torque 150 Nm; FLA 50 Hz 1.9 A | 762A00-11300000/A: Weatherproof; On/Off torque 150 Nm; FLA 50 Hz 2.3 A | 762Y30-11300000/A: Explosionproof; On/Off torque 200 Nm; FLA 50 Hz 2.2 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=17 shown: 762X30-11300000/A, 762A00-11300000/A, 762Y30-11300000/A
    PRODUCT CARD: 762X30-11300000/A | explosionproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762Y30-11300000/A | explosionproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1770; on_off_torque_nm=200
    CHIPS: Compare top 2 | Show all 17
    ACTIVE FILTERS: On/Off service, torque >= 150 Nm, 110 V

## L5-01  (persona: typos-mixed)
Scripted user turns: ["Need a weathrproof actautor, 220 volts, open n close, 150 Nm or more."]

### Variant A
  > USER: Need a weathrproof actautor, 220 volts, open n close, 150 Nm or more.   [3.78 s, HTTP 200]
    ANSWER: 21 actuators meet: Weatherproof, On/Off service, 220 V, torque >= 150 Nm. To narrow it down: number of phases. | Interpreted 'weathrproof' as Weatherproof. | Interpretation: 'open n close' read as On/Off service. | Ranked by closest torque at or above 150 Nm, then lowest FLA. | 762A00-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 1 A | 762B00-11320000/A: On/Off torque 200 Nm; FLA 50 Hz 1.1 A | 763A00-11330C00/A: Shared torque 300 Nm (same torque for On/Off and Modulating); FLA 50 Hz 1 A
    QUESTION CARD: How many phases? 1 phase(14)/3 phase(7)
    RANKED LIST: closest torque at or above 150 Nm, then lowest FLA total=21 shown: 762A00-11320000/A, 762B00-11320000/A, 763A00-11330C00/A
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200
    PRODUCT CARD: 763A00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=2650; shared_torque_nm=300
    CHIPS: Compare top 2 | Show all 21
    ACTIVE FILTERS: Weatherproof, On/Off service, 220 V, torque >= 150 Nm

## L5-02  (persona: typos-mixed)
Scripted user turns: ["Can you get the torque for 762Q99-11300000/A? Please don't swap in a similar code."]

### Variant A
  > USER: Can you get the torque for 762Q99-11300000/A? Please don't swap in a similar code.   [2.13 s, HTTP 200]
    ANSWER: 762Q99-11300000/A is not in the supplied Series 76 electrical catalogue.

## L5-03  (persona: typos-mixed)
Scripted user turns: ["¿Qué tiempo de operación tiene el 761A00-11300000/A a 50 Hz?"]

### Variant A
  > USER: ¿Qué tiempo de operación tiene el 761A00-11300000/A a 50 Hz?   [2.23 s, HTTP 200]
    ANSWER: 761A00-11300000/A |  • Operating time at 50 Hz: 20 s |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 761A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | operating_time_50hz_s=20