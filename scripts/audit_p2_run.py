"""Offline saved-run audit against CSV figures and independently reviewed scopes.

This is a screening audit, not a replacement for blind prose/intent review.
Every flagged eligibility case is retained for explicit human adjudication.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.acceptance_contract import catalogue, eligible_codes, public_cell_matches


def audit(data, scopes):
    rows = catalogue()
    figures, eligibility, invented, layout = [], [], [], []
    checked = 0
    turns = 0
    for conv in data['results']:
        for index, turn in enumerate(conv['turns']):
            response = turn.get('response') or {}
            if turn.get('status') != 200:
                continue
            turns += 1
            location = dict(conversation=conv['id'], turn=index+1, message_id=response.get('message_id'))
            expected = scopes[conv['id']][index]
            for p in response.get('products', []):
                code = p['base_part_number']
                row = rows.get(code)
                if row is None:
                    figures.append(location | dict(code=code, error='unknown card code'))
                    continue
                for field, actual in dict(p.get('measurements', {}),
                    supply_voltage_v=p.get('supply_voltage_v'), phase_count=p.get('phase_count')).items():
                    published = row.get(field, '')
                    checked += 1
                    if (actual is None) != (not published) or (published and Decimal(str(actual)) != Decimal(published)):
                        figures.append(location | dict(code=code, field=field, actual=actual, expected=published))
                for freq in p.get('frequencies', []):
                    suffix = str(freq['frequency_hz'])+'hz' if freq.get('frequency_hz') else 'unqualified'
                    for metric, unit in [('operating_time','s'),('fla','a'),('lra','a')]:
                        field = f'{metric}_{suffix}_{unit}'
                        actual, published = freq.get(metric+'_'+unit), row.get(field, '')
                        checked += 1
                        if (actual is None) != (not published) or (published and Decimal(str(actual)) != Decimal(published)):
                            figures.append(location | dict(code=code, field=field, actual=actual, expected=published))
            comp = response.get('comparison') or {}
            for field in comp.get('rows', []) + comp.get('hidden_rows', []):
                for code, text in zip(comp['models'], field['values']):
                    checked += 1
                    if code not in rows or not public_cell_matches(text, rows[code], field['field']):
                        figures.append(location | dict(code=code, field=field['field'], actual=text))
            rec = response.get('recommendation') or {}
            for item in rec.get('items', []):
                row = rows.get(item['part_number'], {})
                for kv in item.get('key_values', []):
                    label, value = kv['label'].lower(), kv['value']
                    field = None
                    if 'torque' in label:
                        stem = 'shared' if 'shared' in label else 'modulating' if 'modulating' in label else 'on_off'
                        field = stem+'_torque_'+('in_lb' if 'in-lb' in value else 'nm')
                    elif 'motor power' in label: field = 'motor_power_w'
                    elif any(k in label for k in ('fla','lra','operating time')):
                        name = 'operating_time' if 'operating time' in label else 'lra' if 'lra' in label else 'fla'
                        hz = re.search(r'(50|60)\s*hz', label)
                        field = name+'_'+(hz.group(1)+'hz' if hz else 'unqualified')+'_'+('s' if name=='operating_time' else 'a')
                    if field:
                        checked += 1
                        unit = 'in-lb' if field.endswith('_in_lb') else 'Nm' if field.endswith('_nm') else None
                        matches = (value == row.get(field, '') + ' ' + unit) if unit else public_cell_matches(value, row, field)
                        if not matches:
                            figures.append(location | dict(code=item['part_number'],field=field,actual=value))
            cards = [p['base_part_number'] for p in response.get('products', [])]
            ranked = [p['part_number'] for p in rec.get('items', [])]
            if cards and ranked and cards != ranked:
                layout.append(location | dict(cards=cards, ranked=ranked))
            if rec and not ranked:
                layout.append(location | dict(error='empty recommendation payload'))
            # Numeric active filters must have a user-reviewed dimension. A
            # lookup frequency may legitimately appear without being a bound.
            for f in response.get('active_filters', []):
                if f['field'].startswith(('min_','max_')) and f['field'] not in expected:
                    invented.append(location | dict(field=f['field'],label=f['label']))
            if not expected:
                continue
            allowed = set(eligible_codes(expected))
            answer = response.get('answer', '')
            mentioned = set(re.findall(r'\b\d{3}[A-Z0-9]{3}-[A-Z0-9]{8}/A\b', answer))
            codes = set(cards + ranked + comp.get('models', [])) | mentioned
            for code in codes - allowed:
                labelled = bool(re.search(re.escape(code) + r'(?:[^\n]{0,120})\b(?:does not meet|is out:|fails active requirements)',answer,re.I))
                if rec.get('total') == 0 and code in ranked:
                    labelled |= any(p['part_number']==code and re.search(r'does not meet|fails active requirements',p['reason'],re.I)
                                    for p in rec['items'])
                reference = 'Using '+code+' as the reference;' in answer
                if not labelled and not reference:
                    eligibility.append(location | dict(code=code, expected=expected, answer=answer))
    flagged_turns = {(x['conversation'],x['turn']) for x in eligibility+invented}
    return dict(turns=turns, values_checked=checked, wrong_figures=figures,
                eligibility_flags=eligibility, invented_filter_flags=invented,
                layout_flags=layout, flagged_integrity_turns=len(flagged_turns),
                screening_compliance=(turns-len(flagged_turns))/turns if turns else None,
                note='All flags require adjudication against the complete saved answer; prose aggregates and reference drift remain part of blind/human review.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results',type=Path)
    parser.add_argument('--scopes',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=audit(json.loads(args.results.read_text(encoding='utf-8')),
                 json.loads(args.scopes.read_text(encoding='utf-8'))['scopes'])
    result['results_sha256']=hashlib.sha256(args.results.read_bytes()).hexdigest()
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in result.items() if k!='note'}))
    raise SystemExit(bool(result['wrong_figures'] or result['eligibility_flags'] or result['invented_filter_flags']))
