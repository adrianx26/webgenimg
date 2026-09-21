import json
import unittest

import httpx

from perchance_client import PerchanceClient, PerchanceServiceError


class PerchanceClientTests(unittest.TestCase):
    def test_generation_uses_current_contract(self):
        requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path.endswith("/verifyUser"):
                return httpx.Response(200, json={"status": "success", "userKey": "test-key"})
            if request.url.path.endswith("/generate"):
                return httpx.Response(
                    200,
                    json={
                        "status": "success",
                        "imageId": "test-image",
                        "fileExtension": "jpeg",
                        "seed": 42,
                        "prompt": "test prompt",
                        "negativePrompt": "",
                        "width": 512,
                        "height": 512,
                        "guidanceScale": 7.0,
                        "maybeNsfw": False,
                        "imageDownloadUrl": "/api/downloadTemporaryImage?imageId=test-image",
                    },
                )
            raise AssertionError(f"Unexpected request: {request.url}")

        client = PerchanceClient()
        client.client = httpx.Client(transport=httpx.MockTransport(handler))

        result = client.generate("test prompt")
        request_body = json.loads(requests[1].content)

        self.assertEqual(result.image_id, "test-image")
        self.assertEqual(request_body["generatorName"], "ai-image-generator")
        self.assertEqual(request_body["channel"], "ai-text-to-image-generator")

    def test_cloudflare_page_becomes_actionable_service_error(self):
        client = PerchanceClient()
        client.client = httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    403, headers={"content-type": "text/html"}, text="challenge"
                )
            )
        )

        with self.assertRaisesRegex(PerchanceServiceError, "Cloudflare challenge"):
            client.verify_user()


if __name__ == "__main__":
    unittest.main()
