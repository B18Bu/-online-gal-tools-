import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("deepseek_wechat_fallback.py")
SPEC = importlib.util.spec_from_file_location("earth_online_gal_toolkit", MODULE_PATH)
toolkit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = toolkit
SPEC.loader.exec_module(toolkit)


class ChatContextTests(unittest.TestCase):
    def test_uses_latest_left_side_message_and_filters_times(self):
        result = [
            [[(10, 10), (50, 10), (50, 30), (10, 30)], ("12:30", 0.99)],
            [[(20, 50), (180, 50), (180, 80), (20, 80)], ("今晚有空吗", 0.99)],
            [[(300, 100), (470, 100), (470, 130), (300, 130)], ("晚点说", 0.99)],
            [[(30, 150), (210, 150), (210, 180), (30, 180)], ("好呀", 0.99)],
        ]
        context = toolkit.build_chat_context(toolkit.parse_ocr_lines(result), region_width=500)
        self.assertEqual(context.latest_incoming, "好呀")
        self.assertEqual(context.transcript, "对方：今晚有空吗\n我：晚点说\n对方：好呀")

    def test_keeps_full_text_from_current_rapidocr_format(self):
        result = [
            [[(10, 10), (200, 10), (200, 30), (10, 30)], "卑鄙我去吧瞬间就爱上雷神", 0.99],
        ]
        lines = toolkit.parse_ocr_lines(result)
        self.assertEqual(lines[0].text, "卑鄙我去吧瞬间就爱上雷神")

    def test_preserves_no_reply_decision(self):
        response = toolkit.normalize_response(json.dumps({
            "intent": "ignore",
            "should_reply": False,
            "note": "无需继续话题",
            "replies": ["在呢"],
        }))
        self.assertFalse(response["should_reply"])
        self.assertEqual(response["replies"], ["在呢"])

    def test_rejects_response_without_boolean_should_reply(self):
        with self.assertRaises(toolkit.ToolkitError):
            toolkit.normalize_response('{"should_reply": "false"}')

    def test_normalizes_detailed_judgment_for_gui(self):
        response = toolkit.normalize_response(json.dumps({
            "intent": "question",
            "should_reply": True,
            "note": "对方在追问细节",
            "analysis": {
                "question": "是否应该立刻回答具体内容？",
                "yes": -10,
                "no": 30,
                "best_action": "搜索聊天记录",
                "actions": [
                    {"label": "搜索聊天记录", "probability": 120},
                    {"label": "硬猜", "probability": -4},
                    {"label": "转移话题", "probability": 1},
                ],
                "risk_level": 15,
            },
            "replies": ["我先确认一下"],
        }))
        analysis = response["analysis"]
        self.assertEqual((analysis["yes"], analysis["no"]), (0, 100))
        self.assertEqual(analysis["best_action"], "搜索聊天记录")
        self.assertEqual([action["probability"] for action in analysis["actions"]], [99, 0, 1])
        self.assertEqual(analysis["risk_level"], 10)
        self.assertFalse(analysis["is_estimate"])

    def test_uses_labeled_fallback_when_model_omits_detailed_judgment(self):
        response = toolkit.normalize_response(json.dumps({
            "intent": "ignore",
            "should_reply": False,
            "note": "无需继续话题",
            "replies": [],
        }))
        analysis = response["analysis"]
        self.assertTrue(analysis["is_estimate"])
        self.assertEqual(analysis["question"], "是否应该立刻回答具体内容？")
        self.assertEqual(analysis["yes"] + analysis["no"], 100)
        self.assertEqual(analysis["best_action"], "先不回答具体内容")

    def test_explains_deepseek_auth_and_timeout_errors_without_sensitive_data(self):
        class AuthError(Exception):
            status_code = 401

        class RequestTimeout(Exception):
            pass

        self.assertEqual(toolkit.describe_deepseek_error(AuthError()), "API Key 无效或已过期。")
        self.assertEqual(toolkit.describe_deepseek_error(RequestTimeout()), "请求超时，请检查网络后重试。")

    def test_uses_direct_completion_endpoint_and_extracts_content(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"{\\"ok\\":true}"}}]}'

        with patch.object(toolkit.urllib.request, "urlopen", return_value=FakeResponse()) as urlopen:
            content = toolkit.request_deepseek_completion(
                "test-key",
                [{"role": "user", "content": "连接测试"}],
                timeout=1,
                max_tokens=16,
                temperature=0,
                response_format={"type": "json_object"},
            )
        request = urlopen.call_args.args[0]
        self.assertEqual(content, '{"ok":true}')
        self.assertEqual(request.full_url, toolkit.DEEPSEEK_COMPLETIONS_URL)
        self.assertEqual(request.get_method(), "POST")

    def test_builds_compact_prompt_without_fstring_format_errors(self):
        prompt = toolkit.build_system_prompt("friend")
        schema_text = prompt.split("只输出紧凑 JSON，不要 Markdown：\n", 1)[1].split("\n\n规则：", 1)[0]
        schema = json.loads(schema_text)
        self.assertEqual(schema["analysis"]["best_action"], "直接回答")
        self.assertEqual(len(schema["analysis"]["actions"]), 3)
        self.assertEqual(schema["replies"], ["候选1", "候选2", "候选3"])
        self.assertIn("不要主动安慰", prompt)
        self.assertIn("轻度口语粗话", prompt)

    def test_rejects_invalid_region(self):
        with self.assertRaises(toolkit.ToolkitError):
            toolkit.validate_region((0, 0, 0, 100))

    def test_loads_only_deepseek_key_from_dotenv(self):
        with tempfile.TemporaryDirectory() as directory:
            dotenv_path = Path(directory) / ".env"
            dotenv_path.write_text("OTHER_KEY=ignore\nDEEPSEEK_API_KEY='test-key'\n", encoding="utf-8")
            self.assertEqual(toolkit.load_dotenv_api_key(dotenv_path), "test-key")


if __name__ == "__main__":
    unittest.main()
