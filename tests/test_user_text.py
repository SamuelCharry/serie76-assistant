"""Guard public prose against internal protocol and unsupported ratings."""
import re
import unittest


FORBIDDEN = re.compile(
    r"\b(?:Not applied|get_actuator|search_actuators|ask_clarification|explain_terms|"
    r"on_off|explosionproof|weatherproof|modulating|(?:[a-z]+_){1,}[a-z0-9]+|"
    r"NEMA|IP\s*\d+)\b|[{}]",
)


def visible_texts(response):
    """Walk only human-readable fields; IDs and option values are machine data."""
    def visit(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            for item in value:
                yield from visit(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                if key in {'answer', 'lead', 'label', 'reason', 'prompt', 'message', 'summary', 'suggested_replies', 'values'}:
                    yield from visit(item)
                elif isinstance(item, dict):
                    yield from visit(item)
                elif isinstance(item, list):
                    for nested in item:
                        if isinstance(nested, dict):
                            yield from visit(nested)
    return list(visit(response))


def assert_public_text_clean(response):
    for value in visible_texts(response):
        match = FORBIDDEN.search(value)
        if match:
            raise AssertionError(f"Forbidden public text: {match.group(0)}")


class PublicTextTests(unittest.TestCase):
    def test_clean_example(self):
        assert_public_text_clean({'answer': "Assumed AC, single-phase supply. Tell me if that's wrong."})

    def test_mutations_fail(self):
        for mutation in ('Not applied', 'min_torque_nm', 'get_actuator', 'IP67', '{service}', 'explosionproof'):
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                assert_public_text_clean({'answer': mutation})
