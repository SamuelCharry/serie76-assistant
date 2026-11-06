
## L1-01  (persona: precise)
Scripted user turns: ["Please report the 50 Hz travel time of 761A00-11300000/A."]

### Variant A
  > USER: Please report the 50 Hz travel time of 761A00-11300000/A.   [2.62 s, HTTP 200]
    ANSWER: 761A00-11300000/A |  • Operating time at 50 Hz: 20 s |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 761A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | operating_time_50hz_s=20

## L1-02  (persona: precise)
Scripted user turns: ["For 762B00-11320000/A, what is the on/off torque in Nm?", "What is its modulating torque in the same unit?"]

### Variant A
  > USER: For 762B00-11320000/A, what is the on/off torque in Nm?   [2.57 s, HTTP 200]
    ANSWER: 762B00-11320000/A |  • On/Off torque: 1750 in-lb / 200 Nm |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 762B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200
  > USER: What is its modulating torque in the same unit?   [2.87 s, HTTP 200]
    ANSWER: 762B00-11320000/A |  • Modulating torque: 1330 in-lb / 150 Nm |  Source: Series 76 electrical catalogue, page 1.
    PRODUCT CARD: 762B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | modulating_torque_in_lb=1330; modulating_torque_nm=150

## L1-03  (persona: precise)
Scripted user turns: ["Read out the motor wattage and 60 Hz full-load current for 763A00-11300000/A."]

### Variant A
  > USER: Read out the motor wattage and 60 Hz full-load current for 763A00-11300000/A.   [2.31 s, HTTP 200]
    ANSWER: 763A00-11300000/A |  • Motor power: 40 W |  • FLA at 60 Hz: 2.6 A |  Source: Series 76 electrical catalogue, page 1. | Motor power is the rated power of the internal motor; the catalogue does not publish total electrical consumption.
    PRODUCT CARD: 763A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | motor_power_w=40; fla_60hz_a=2.6

## L1-04  (persona: precise)
Scripted user turns: ["Put 761A00-11300000/A beside 761B00-11300000/A and compare their on/off torque and 50 Hz travel time."]

### Variant A
  > USER: Put 761A00-11300000/A beside 761B00-11300000/A and compare their on/off torque and 50 Hz travel time.   [2.13 s, HTTP 200]
    ANSWER: Comparing 761A00-11300000/A vs 761B00-11300000/A. 10 identical fields hidden. | On/Off torque: 700 in-lb / 80 Nm vs 880 in-lb / 100 Nm | Modulating torque: 580 in-lb / 65 Nm vs 620 in-lb / 70 Nm | On/Off cycles: 36 /h vs 31 /h | Operating time at 50 Hz: 20 s vs 23 s | FLA at 50 Hz: 1.1 A vs 1.2 A | Operating time at 60 Hz: 17 s vs 19 s | FLA at 60 Hz: 1.2 A vs 1.3 A
    COMPARISON: models=['761A00-11300000/A', '761B00-11300000/A'] summary=761A00-11300000/A wins 5 of 7 differing fields with an agreed direction; 761B00-11300000/A wins 2. This is an unweighted field count, not an overall suitability rating.

## L1-05  (persona: precise)
Scripted user turns: ["List the explosionproof units that accept a 24 V DC supply, including dual AC/DC units."]

### Variant A
  > USER: List the explosionproof units that accept a 24 V DC supply, including dual AC/DC units.   [2.07 s, HTTP 200]
    ANSWER: 5 actuators meet: Explosionproof, AC/DC, 24 V. Here are the leading published models. | Ranked by lowest FLA, then shortest operating time. | 761X30-11380000/A: On/Off torque 70 Nm; FLA 5 A | 762X30-11380000/A: On/Off torque 150 Nm; FLA 6 A | 761Y30-11380000/A: On/Off torque 80 Nm; FLA 6.3 A
    RANKED LIST: lowest FLA, then shortest operating time total=5 shown: 761X30-11380000/A, 762X30-11380000/A, 761Y30-11380000/A
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=1350; on_off_torque_nm=150
    PRODUCT CARD: 761Y30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    CHIPS: Compare top 2 | Show all 5
    ACTIVE FILTERS: Explosionproof, 24 V, AC/DC

## L1-06  (persona: precise)
Scripted user turns: ["Select 24 V units whose supply type is DC only; exclude every AC/DC entry."]

### Variant A
  > USER: Select 24 V units whose supply type is DC only; exclude every AC/DC entry.   [1.89 s, HTTP 200]
    ANSWER: 5 actuators meet: DC, DC-only models, 24 V. | Ranked by lowest FLA, then shortest operating time. | 761X30-11370000/A: Explosionproof; Modulating torque 65 Nm; FLA (DC) 5 A | 762X30-11370000/A: Explosionproof; Modulating torque 130 Nm; FLA (DC) 6 A | 761Y30-11370000/A: Explosionproof; Modulating torque 72 Nm; FLA (DC) 6.3 A | 762Y30-11370000/A: Explosionproof; Modulating torque 145 Nm; FLA (DC) 7.4 A | 763X30-11370000/A: Explosionproof; Modulating torque 220 Nm; FLA (DC) 8.9 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas. | DC-only eligibility excludes AC/DC models.
    RANKED LIST: lowest FLA, then shortest operating time total=5 shown: 761X30-11370000/A, 762X30-11370000/A, 761Y30-11370000/A, 762Y30-11370000/A, 763X30-11370000/A
    CHIPS: Compare top 2
    ACTIVE FILTERS: DC-only models, 24 V, DC

## L1-07  (persona: precise)
Scripted user turns: ["For 762A00-11330C00/A, report the published motor power and torque even if the table has no numeric value."]

### Variant A
  > USER: For 762A00-11330C00/A, report the published motor power and torque even if the table has no numeric value.   [2.39 s, HTTP 200]
    ANSWER: 762A00-11330C00/A | 762A00-11330C00/A — Weatherproof, 220 V AC 3-phase: every performance value of this row is N/A in the source table; nothing can be inferred. | Motor power is the rated power of the internal motor; the catalogue does not publish total electrical consumption.
    PRODUCT CARD: 762A00-11330C00/A | weatherproof | 220 V AC | 3-phase | source_NA | 

## L2-01  (persona: layperson)
Scripted user turns: ["I'm new to these actuators. What kinds of jobs does Series 76 cover?"]

### Variant A
  > USER: I'm new to these actuators. What kinds of jobs does Series 76 cover?   [2.67 s, HTTP 200]
    ANSWER: Series 76 Electric Actuators: The data provided pertains to the Series 76, a line of heavy-duty electric actuators. These devices are critical components in industrial automation, used to remotely open, close, or precisely control valves and dampers in a wide range of applications, from HVAC systems to industrial processing plants. [Series 76 summary, p. 1]

## L2-02  (persona: layperson)
Scripted user turns: ["Our garden water valve just needs to open and shut. The power nearby is 110 volts.", "It sits outdoors and there are no flammable materials around."]

### Variant A
  > USER: Our garden water valve just needs to open and shut. The power nearby is 110 volts.   [2.85 s, HTTP 200]
    ANSWER: 21 actuators meet: On/Off service, 110 V. To narrow it down: enclosure. | Please confirm enclosure if it matters for your choice. | Interpretation: 'open and shut' read as On/Off service. | Ranked by lowest FLA, then shortest operating time. | 761A00-11300000/A: Weatherproof; On/Off torque 80 Nm; FLA 50 Hz 1.1 A | 761X30-11300000/A: Explosionproof; On/Off torque 80 Nm; FLA 50 Hz 1.1 A | 761Y30-11300000/A: Explosionproof; On/Off torque 100 Nm; FLA 50 Hz 1.1 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    QUESTION CARD: Which enclosure? Explosionproof(10)/Weatherproof(11)
    RANKED LIST: lowest FLA, then shortest operating time total=21 shown: 761A00-11300000/A, 761X30-11300000/A, 761Y30-11300000/A
    PRODUCT CARD: 761A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    PRODUCT CARD: 761X30-11300000/A | explosionproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=690; on_off_torque_nm=80
    PRODUCT CARD: 761Y30-11300000/A | explosionproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=860; on_off_torque_nm=100
    CHIPS: Compare top 2 | Show all 21
    ACTIVE FILTERS: On/Off service, 110 V
  > USER: It sits outdoors and there are no flammable materials around.   [0.11 s, HTTP 200]
    ANSWER: 11 actuators meet: Weatherproof, On/Off service, 110 V. To narrow it down: minimum torque. | Ranked by lowest FLA, then shortest operating time. | 761A00-11300000/A: On/Off torque 80 Nm; FLA 50 Hz 1.1 A | 761B00-11300000/A: On/Off torque 100 Nm; FLA 50 Hz 1.2 A | 762A00-11300000/A: On/Off torque 150 Nm; FLA 50 Hz 2.3 A
    QUESTION CARD: What minimum torque do you need? 150 Nm or more(9)/500 Nm or more(6)/1100 Nm or more(3)
    RANKED LIST: lowest FLA, then shortest operating time total=11 shown: 761A00-11300000/A, 761B00-11300000/A, 762A00-11300000/A
    PRODUCT CARD: 761A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80
    PRODUCT CARD: 761B00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100
    PRODUCT CARD: 762A00-11300000/A | weatherproof | 110 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    CHIPS: Compare top 2 | Show all 11
    ACTIVE FILTERS: On/Off service, 110 V, Weatherproof

## L2-03  (persona: layperson)
Scripted user turns: ["Can you explain the difference between opening a valve fully and adjusting it partway?"]

### Variant A
  > USER: Can you explain the difference between opening a valve fully and adjusting it partway?   [2.89 s, HTTP 200]
    ANSWER: On/Off: The actuator operates in two positions: fully open or fully closed. [Series 76 summary, p. 1]

## L2-04  (persona: layperson)
Scripted user turns: ["I have a 220 volt supply in an ordinary pump shed. Help me start choosing an actuator.", "The valve needs 100 Nm and only opens or closes."]

### Variant A
  > USER: I have a 220 volt supply in an ordinary pump shed. Help me start choosing an actuator.   [6.15 s, HTTP 200]
    ANSWER: 23 actuators meet: Weatherproof, 220 V. To narrow it down: number of phases. | Interpretation: 'ordinary pump shed' read as Weatherproof. | Ranked by lowest FLA, then shortest operating time. | 761A00-11320000/A: On/Off torque 80 Nm; Modulating torque 65 Nm; FLA 50 Hz 0.7 A | 761B00-11320000/A: On/Off torque 100 Nm; Modulating torque 70 Nm; FLA 50 Hz 0.7 A | 762A00-11320000/A: On/Off torque 150 Nm; Modulating torque 130 Nm; FLA 50 Hz 1 A
    QUESTION CARD: How many phases? 1 phase(16)/3 phase(7)
    RANKED LIST: lowest FLA, then shortest operating time total=23 shown: 761A00-11320000/A, 761B00-11320000/A, 762A00-11320000/A
    PRODUCT CARD: 761A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=700; on_off_torque_nm=80; modulating_torque_in_lb=580; modulating_torque_nm=65
    PRODUCT CARD: 761B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100; modulating_torque_in_lb=620; modulating_torque_nm=70
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150; modulating_torque_in_lb=1150; modulating_torque_nm=130
    CHIPS: Compare top 2 | Show all 23
    ACTIVE FILTERS: Weatherproof, 220 V
  > USER: The valve needs 100 Nm and only opens or closes.   [2.51 s, HTTP 200]
    ANSWER: 22 actuators meet: Weatherproof, On/Off service, 220 V, torque >= 100 Nm. To narrow it down: number of phases. | Interpretation: 'only opens or closes' read as On/Off service. | Ranked by closest torque at or above 100 Nm, then lowest FLA. | 761B00-11320000/A: On/Off torque 100 Nm; FLA 50 Hz 0.7 A | 762A00-11320000/A: On/Off torque 150 Nm; FLA 50 Hz 1 A | 762B00-11320000/A: On/Off torque 200 Nm; FLA 50 Hz 1.1 A
    QUESTION CARD: How many phases? 1 phase(15)/3 phase(7)
    RANKED LIST: closest torque at or above 100 Nm, then lowest FLA total=22 shown: 761B00-11320000/A, 762A00-11320000/A, 762B00-11320000/A
    PRODUCT CARD: 761B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=880; on_off_torque_nm=100
    PRODUCT CARD: 762A00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1330; on_off_torque_nm=150
    PRODUCT CARD: 762B00-11320000/A | weatherproof | 220 V AC | 1-phase | reported | on_off_torque_in_lb=1750; on_off_torque_nm=200
    CHIPS: Compare top 2 | Show all 22
    ACTIVE FILTERS: Weatherproof, 220 V, On/Off service, torque >= 100 Nm

## L2-05  (persona: layperson)
Scripted user turns: ["How long does 761B00-11300000/A take to move at 50 Hz?"]

### Variant A
  > USER: How long does 761B00-11300000/A take to move at 50 Hz?   [0.07 s, HTTP 200]
    ANSWER: That isn't published in the Series 76 catalogue. I can show its published specifications.

## L2-06  (persona: layperson)
Scripted user turns: ["Does 762A00-11300000/A have a weatherproof enclosure?"]

### Variant A
  > USER: Does 762A00-11300000/A have a weatherproof enclosure?   [0.07 s, HTTP 200]
    ANSWER: Published enclosures: Explosionproof (30 models), Weatherproof (34 models).

## L2-07  (persona: layperson)
Scripted user turns: ["I only have a battery supplying 24 volts. Which units can work from that?"]

### Variant A
  > USER: I only have a battery supplying 24 volts. Which units can work from that?   [2.63 s, HTTP 200]
    ANSWER: 10 actuators meet: DC, 24 V. Here are the leading published models. | Please confirm DC-only models if it matters for your choice. | Solar or battery supply is DC; compatible AC/DC models remain eligible. | Ranked by lowest FLA, then shortest operating time. | 761X30-11370000/A: Explosionproof; Modulating torque 65 Nm; FLA (DC) 5 A | 761X30-11380000/A: Explosionproof; On/Off torque 70 Nm; FLA 5 A | 762X30-11370000/A: Explosionproof; Modulating torque 130 Nm; FLA (DC) 6 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas. | For a DC supply, compatible AC/DC models remain eligible.
    RANKED LIST: lowest FLA, then shortest operating time total=10 shown: 761X30-11370000/A, 761X30-11380000/A, 762X30-11370000/A
    PRODUCT CARD: 761X30-11370000/A | explosionproof | 24 V DC | reported | modulating_torque_in_lb=560; modulating_torque_nm=65
    PRODUCT CARD: 761X30-11380000/A | explosionproof | 24 V AC/DC | reported | on_off_torque_in_lb=620; on_off_torque_nm=70
    PRODUCT CARD: 762X30-11370000/A | explosionproof | 24 V DC | reported | modulating_torque_in_lb=1150; modulating_torque_nm=130
    CHIPS: Compare top 2 | Show all 10
    ACTIVE FILTERS: DC, 24 V

## L2-08  (persona: layperson)
Scripted user turns: ["Which supply voltages are listed in this catalogue?", "Are there three-phase options too?"]

### Variant A
  > USER: Which supply voltages are listed in this catalogue?   [0.06 s, HTTP 200]
    ANSWER: 3 published supply voltages: 24 V (10 models), 110 V (21 models), 220 V (33 models).
  > USER: Are there three-phase options too?   [5.41 s, HTTP 200]
    ANSWER: 7 actuators meet: 3-phase. Here are the leading published models. | Ranked by lowest FLA, then shortest operating time. | 763A00-11330C00/A: Weatherproof; Shared torque 300 Nm (same torque for On/Off and Modulating); FLA 50 Hz 1 A | 763B00-11330C00/A: Weatherproof; Shared torque 500 Nm (same torque for On/Off and Modulating); FLA 50 Hz 2 A | 763C00-11330C00/A: Weatherproof; Shared torque 600 Nm (same torque for On/Off and Modulating); FLA 50 Hz 2 A | Enclosure not specified: Weatherproof is for general areas; choose Explosionproof for hazardous areas.
    RANKED LIST: lowest FLA, then shortest operating time total=7 shown: 763A00-11330C00/A, 763B00-11330C00/A, 763C00-11330C00/A
    PRODUCT CARD: 763A00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=2650; shared_torque_nm=300
    PRODUCT CARD: 763B00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=4400; shared_torque_nm=500
    PRODUCT CARD: 763C00-11330C00/A | weatherproof | 220 V AC | 3-phase | reported | shared_torque_in_lb=5300; shared_torque_nm=600
    CHIPS: Compare top 2 | Show all 7
    ACTIVE FILTERS: 3-phase