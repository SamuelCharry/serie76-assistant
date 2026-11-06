"""Offline uncertainty for strict conversation verdicts; standard library only.

Resample whole conversations, not turns. Aggregate counts suffice for a binary
pass-rate interval, but cannot recover paired disagreements. Rounds stay separate.
These intervals describe sampling uncertainty, not reviewer bias or future drift.
"""
import argparse
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261104
RESAMPLES = 10_000


def percentile(values, probability):
    """Linearly interpolate between adjacent sorted sample values."""
    position = (len(values) - 1) * probability
    low = math.floor(position)
    high = math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def bootstrap_ci(values, *, seed=SEED, resamples=RESAMPLES):
    """For A/B, pass A-minus-B per conversation so pairs stay together."""
    if not values or resamples < 2:
        raise ValueError('Need observations and at least two resamples')
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values)
                   for _ in range(resamples))
    return [percentile(means, .025), percentile(means, .975)]


def mcnemar_exact(only_a, only_b):
    """Under no difference, each discordant pair is a fair coin flip."""
    if any(type(x) is not int or x < 0 for x in (only_a, only_b)):
        raise ValueError('Discordant counts must be nonnegative integers')
    n = only_a + only_b
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(only_a, only_b) + 1)) / 2**n)


def minimum_one_way(n):
    """All other pairs agree; every disagreement favors the same setup."""
    return next((d for d in range(1, n + 1) if mcnemar_exact(d, 0) < .05), None)


def pass_summary(label, values):
    if not values or any(type(v) is not int or v not in (0, 1) for v in values):
        raise ValueError('Verdicts must be a nonempty list of integer zeros and ones')
    return dict(configuration=label, passed=sum(values), n=len(values),
                pass_rate=sum(values) / len(values), ci95=bootstrap_ci(values))


def evaluate(data):
    configurations, comparisons = [], []
    for row in data['aggregate_rounds']:
        p, n = row['passed'], row['total']
        if any(type(v) is not int for v in (p, n)) or not 0 <= p <= n or n == 0:
            raise ValueError('Invalid aggregate counts')
        configurations.append(pass_summary(f"round{row['round']}/{row['config']}", [1]*p + [0]*(n-p)))
    for label, conversations in data['paired'].items():
        if not conversations:
            raise ValueError('Empty paired cohort')
        names = list(next(iter(conversations.values())))
        if len(names) != 2 or any(set(row) != set(names) for row in conversations.values()):
            raise ValueError('Each conversation must have the same two configurations')
        a, b = ([row[name] for row in conversations.values()] for name in names)
        configurations.extend(pass_summary(f'{label}/{name}', values)
                              for name, values in zip(names, (a, b)))
        only_a = sum(x == 1 and y == 0 for x, y in zip(a, b))
        only_b = sum(x == 0 and y == 1 for x, y in zip(a, b))
        differences = [x-y for x, y in zip(a, b)]
        p_value = mcnemar_exact(only_a, only_b)
        comparisons.append(dict(comparison=label, a=names[0], b=names[1], n=len(a),
                                only_a=only_a, only_b=only_b, p_value=p_value,
                                difference=sum(differences)/len(a), ci95=bootstrap_ci(differences),
                                minimum_one_way=minimum_one_way(len(a)),
                                verdict=('significant' if p_value < .05 else
                                         'not significant: the difference is within sampling noise')))
    return dict(seed=SEED, resamples=RESAMPLES, method='percentile bootstrap, whole conversations',
                configurations=configurations, paired=comparisons)


def interval(ci):
    return f'[{100*ci[0]:.1f}, {100*ci[1]:.1f}]'


def readable(result):
    lines = [f"95% percentile bootstrap; {result['resamples']:,} resamples; seed {result['seed']}."]
    for row in result['configurations']:
        lines.append(f"{row['configuration']}: {row['passed']}/{row['n']} = "
                     f"{100*row['pass_rate']:.1f}%; CI {interval(row['ci95'])}%")
    for row in result['paired']:
        lines.extend([f"{row['comparison']} (A={row['a']}, B={row['b']}): "
                      f"only A={row['only_a']}, only B={row['only_b']}; exact McNemar p={row['p_value']:.6f}.",
                      f"A-B={100*row['difference']:.2f} percentage points; CI {interval(row['ci95'])} points; {row['verdict']}.",
                      f"At n={row['n']}, at least {row['minimum_one_way']} disagreements all favoring one setup "
                      '(all other pairs agree) are needed for two-sided p < 0.05; this is not a power calculation.'])
    lines.append('Failure to reject is not proof of equivalence; aggregate-only rounds have no paired test.')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('verdicts', nargs='?', type=Path, default=ROOT / 'reports/behavior/verdicts.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'reports/behavior/stats.json')
    args = parser.parse_args()
    result = evaluate(json.loads(args.verdicts.read_text(encoding='utf-8-sig')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(readable(result))


if __name__ == '__main__':
    main()
