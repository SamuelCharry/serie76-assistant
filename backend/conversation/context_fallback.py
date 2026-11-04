"""Compatibility-only lexical fallback for disabled/unavailable semantic retrieval.

Keep this bounded: new paraphrases belong in concept anchors, not more regexes.
"""
import re

HAZARD_RE = re.compile(r'\b(?:flammable|combustible|explosive|solvent|fumes?|vapou?rs?|propane|butane|lpg|natural gas|methane|hydrogen|ammonia|acetylene|gas|dust|atex|iecex|classified (?:zone|area)|hazardous|zone\s*(?:0|1|2|21|22)|class\s*(?:i|ii)\s*div\s*[12]|refinery|petrochemical|mine|mining|distillery|spirits area)\b', re.I)

def colloquial(text):
    result = {}
    if re.search(r'\b(open and close|open and shut|open/shut|open or shut|open or close|fully open|abrir y cerrar|on/of|onoff|on off|on-off)\b', text):
        result['service'] = 'on_off'
    if re.search(r'\b(stop halfway|intermediate positions?|partial positions?|set to partial|mixing positions?|position anywhere|any position|regulat(?:e|ing)|regule|regular caudal|throttl\w*|a medias|control the flow precisely|que module|\d+\s*%\s*open|hold at \d+\s*%\s*open|mod(?=\s|\d))\b', text):
        result['service'] = 'modulating'
    if re.search(r'\b(outside|exteriores?|intemperie)\b|\boutdoors\b.*\bnot hazardous\b', text):
        result['enclosure'] = 'weatherproof'
    if re.search(r'\bnot (?:a )?classified area\b', text):
        result['enclosure'] = 'weatherproof'
    return result

CONTEXT_LEXICON = {
    ("enclosure", "explosionproof"): ("explosion", "hazardous", "atex", "iecex", "flammable", "class i", "zone 1", "antiexplos"),
    ("enclosure", "weatherproof"): ("weatherproof", "weather proof", "weather-proof", "outdoor", "rain", "intemperie", "exteriores"),

    ("service", "on_off"): ("on/off", "on_off", "on-off", "on off", "open/close", "open-close", "open or close",
                            "fully open", "fully closed", "two-position", "two position", "isolation", "todo/nada", "todo o nada",
                            "abrir completo o cerrar completo", "abrir completamente o cerrar completamente"),
    ("service", "modulating"): ("modulat", "positioning", "throttl", "proportional", "intermediate position", "modulante"),
}

def weather_exposure(text):
    return bool(re.search(r'\b(outdoor|rain|exteriores|intemperie|offshore platform)\b', text, re.I))
