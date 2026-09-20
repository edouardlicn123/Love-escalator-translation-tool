import unittest

from pyopencode.subprocess_client import parse_output


class TestParseOutput(unittest.TestCase):
    def test_extracts_text_parts(self):
        lines = [
            '{"type":"step_start","sessionID":"ses_abc","part":{"type":"step-start"}}',
            '{"type":"text","sessionID":"ses_abc","part":{"type":"text","text":"你好"}}',
            '{"type":"text","sessionID":"ses_abc","part":{"type":"text","text":"世界"}}',
            '{"type":"step_finish","sessionID":"ses_abc","part":{"type":"step-finish"}}',
        ]
        text, sid = parse_output(lines)
        self.assertEqual(text, "你好\n世界")
        self.assertEqual(sid, "ses_abc")

    def test_ignores_non_text_events(self):
        lines = [
            '{"type":"reasoning","sessionID":"ses_x","part":{"type":"reasoning","text":"think"}}',
            '{"type":"tool","sessionID":"ses_x","part":{"type":"tool"}}',
        ]
        text, sid = parse_output(lines)
        self.assertEqual(text, "")
        self.assertEqual(sid, "ses_x")

    def test_skips_garbage_lines(self):
        lines = ["not json", "", '{"type":"text","part":{"type":"text","text":"ok"}}']
        text, _ = parse_output(lines)
        self.assertEqual(text, "ok")

    def test_empty_input(self):
        text, sid = parse_output([])
        self.assertEqual(text, "")
        self.assertIsNone(sid)


if __name__ == "__main__":
    unittest.main()