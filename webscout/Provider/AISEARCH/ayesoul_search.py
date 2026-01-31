import asyncio
import json
import queue
import random
import string
import threading
from datetime import datetime
from typing import Any, Dict, Generator, Optional, Union, cast

import aiohttp
import requests

from webscout import exceptions
from webscout.AIbase import AISearch, Response, SearchResponse
from webscout.litagent import LitAgent


class AyeSoul(AISearch):
    """AyeSoul websocket search provider.

    Mirrors the behaviour of other AISEARCH providers: supports both
    streaming and non-streaming 'search' method and returns SearchResponse
    objects or yields chunks for streaming.
    """

    required_auth = False
    AVAILABLE_MODELS = ["DEFAULT"]

    def __init__(self, timeout: int = 60):
        self.url = "wss://goto.ayesoul.com/"
        self.origin = "https://ayesoul.com"
        self.timeout = timeout
        self.agent = LitAgent()
        self.headers = {
            "user-agent": self.agent.random(),
            "origin": self.origin,
            "referer": f"{self.origin}/",
            "accept": "*/*",
            "connection": "keep-alive",
        }
        self.session = requests.Session()
        self.last_response = {}

    def upload_image(self, image_url: str) -> Dict[str, str]:
        try:
            resp = self.session.get(image_url, stream=True, timeout=self.timeout, verify=False)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            image_name = f"IMG-{int(datetime.now().timestamp() * 1000)}.jpg"
            files = {"file": (image_name, resp.content, content_type)}
            xcs = f"{self._gen_id(7)}-|BANKAI|-{self._gen_id(7)}"
            upload_resp = self.session.post(
                "https://ayesoul.com/api/attachgoto",
                files=files,
                headers={
                    "accept": "*/*",
                    "origin": self.origin,
                    "x-cache-sec": xcs,
                    "user-agent": self.headers.get("user-agent"),
                },
                timeout=self.timeout,
                verify=False,
            )
            upload_resp.raise_for_status()
            data = upload_resp.json()
            return {"file_id": data["file_id"], "imageName": image_name, "contentType": content_type}
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Failed to upload image: {e}")

    def _build_payload(
        self, prompt: str, follow_up: bool = False, cid: Optional[str] = None, question: Optional[str] = None, answer: Optional[str] = None, image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        now = datetime.now()
        payload = {
            "event": prompt,
            "dateObject": now.strftime("%A, %B %d, %Y, %I:%M %p"),
            "currentDateTimeISOString": now.isoformat(),
            "id": self._gen_id(),
            "x-cache-sec": f"{self._gen_id(7)}-|BANKAI|-{self._gen_id(7)}",
            "chin_tapak_dum_dum": {"cf_config": {"unos": "", "dos": "", "tres": "", "chin": ""}},
            "nostal": [{"id": cid, "rank": 1, "question": question, "answer": answer}] if follow_up and cid else [],
            "ultra_mode": True,
            "customExcludeList": [],
        }

        if image_url:
            info = self.upload_image(image_url)
            payload["attach"] = [
                {"file_id": info["file_id"], "name": info["imageName"], "type": info["contentType"].split("/")[1], "mime": info["contentType"]}
            ]
        return payload

    async def _ws_worker(self, payload: Dict[str, Any], out_q: "queue.Queue[Optional[tuple]]") -> None:
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.ws_connect(self.url, timeout=self.timeout) as ws:
                    await ws.send_str(json.dumps({"input": json.dumps(payload)}))
                    temp: Dict[str, list] = {}
                    while True:
                        msg = await ws.receive()
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                res = json.loads(msg.data)
                            except Exception:
                                continue
                            key = self.map_status(res.get("status"))
                            if key:
                                temp.setdefault(key, []).append(
                                    json.dumps(res.get("message", "")) if isinstance(res.get("message"), dict) else str(res.get("message", ""))
                                )
                                out_q.put(("chunk", key, temp[key][-1]))
                            if res.get("status") == "SOUL XOver":
                                final = {k: "".join(v) for k, v in temp.items() if "".join(v).strip()}
                                for k in final:
                                    try:
                                        final[k] = json.loads(final[k])
                                    except Exception:
                                        pass
                                out_q.put(("final", final))
                                break
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
        except Exception as e:
            out_q.put(("error", str(e)))
        finally:
            out_q.put(None)

    def _ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: Optional[str] = None,
        conversationally: bool = False,
        **kwargs: Any,
    ) -> Response:
        payload = self._build_payload(prompt, kwargs.get("follow_up", False), kwargs.get("id"), kwargs.get("question"), kwargs.get("answer"), kwargs.get("image_url"))

        if stream:
            def stream_gen() -> Generator[Union[str, Dict[str, Any]], None, None]:
                q: "queue.Queue[Optional[tuple]]" = queue.Queue()

                def runner():
                    try:
                        asyncio.run(self._ws_worker(payload, q))
                    except Exception as e:
                        q.put(("error", str(e)))
                        q.put(None)

                t = threading.Thread(target=runner, daemon=True)
                t.start()

                while True:
                    item = q.get()
                    if item is None:
                        break
                    typ = item[0]
                    if typ == "chunk":
                        _, key, data = item
                        yield data
                    elif typ == "final":
                        _, final = item
                        if isinstance(self.last_response, dict):
                            self.last_response.update(final)
                        # else: do not update if not a dict
                        yield final
                    elif typ == "error":
                        _, err = item
                        raise exceptions.APIConnectionError(err)
                t.join()

            return stream_gen()

        async def run_and_get():
            out_q: "queue.Queue[Optional[tuple]]" = queue.Queue()
            await self._ws_worker(payload, out_q)
            final_result: Dict[str, Any] = {}
            while True:
                it = out_q.get()
                if it is None:
                    break
                if it[0] == "final":
                    final_result = it[1]
                if it[0] == "error":
                    raise exceptions.APIConnectionError(it[1])
            return final_result

        try:
            final = asyncio.run(run_and_get())
            if isinstance(self.last_response, dict):
                self.last_response.update(final)
            # else: do not update if not a dict
            return final
        except Exception as e:
            raise exceptions.FailedToGenerateResponseError(f"Failed to generate response: {e}")

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None]]:
        if not stream:
            result = self._ask(prompt, stream=False, raw=raw, **kwargs)
            if not isinstance(result, dict):
                text = str(result)
            else:
                if isinstance(result, dict):
                    text = self.get_message(result)
                else:
                    text = str(result)
                self.last_response = SearchResponse(text)
                return self.last_response

        def sync_generator():
            buffer = ""
            gen = self._ask(prompt, stream=True, raw=raw, **kwargs)
            for item in gen:
                if isinstance(item, dict):
                    final_text = self.get_message(item)
                    self.last_response = SearchResponse(final_text)
                    if raw:
                        # Ensure yielded dict is dict[str, str]
                        yield {str(k): str(v) for k, v in item.items()}
                    else:
                        yield self.last_response
                else:
                    chunk_text = str(item)
                    buffer += chunk_text
                    if raw:
                        yield {"text": chunk_text}
                    else:
                        yield SearchResponse(chunk_text)
            self.last_response = SearchResponse(buffer)

        return sync_generator()

    def get_message(self, response: Response) -> str:
        """Extract readable text from the provider response.

        Prefer the 'stream' key (AyeSoul places actual text there), then fall
        back to 'answer' or 'finished' keys, then join stringifiable values.
        """
        if isinstance(response, dict):
            resp_dict = cast(Dict[str, Any], response)
            # Prefer 'stream' key which contains the actual message
            if "stream" in resp_dict:
                val = cast(str, resp_dict["stream"])
                if isinstance(val, (dict, list)):
                    try:
                        return json.dumps(val)
                    except Exception:
                        return str(val)
                return str(val)
            # if "answer" in resp_dict:
            #     return str(resp_dict.get("answer"))
            # if "finished" in resp_dict:
            #     return str(resp_dict.get("finished"))
            out = []
            for v in resp_dict.values():
                try:
                    out.append(str(v))
                except Exception:
                    pass
            return "\n".join(out)
        return str(response)

    def _gen_id(self, length: int = 21) -> str:
        chars = string.ascii_letters + string.digits + "_"
        return "".join(random.choice(chars) for _ in range(length))

    def map_status(self, status: Optional[str]) -> Optional[str]:
        mapping = {
            "SOUL XLyze": "analyze",
            "SOUL XCon": "context",
            "SOUL XCraft": "answer",
            "SOUL XOver": "finished",
            "SOUL XErr": "error",
            "SOUL XStream": "stream",
            "SOUL XDots": "dots",
            "SOUL XMeta": "metadata",
            "SOUL XImage": "image",
            "SOUL XType": "type",
            "SOUL Step": "step",
            "sOUL stock": "stock_chart",
        }
        return mapping.get(status)


if __name__ == "__main__":
    from rich import print
    ai = AyeSoul()
    response = ai.search("What is AI?", stream=True, raw=False)
    if hasattr(response, "__iter__") and not isinstance(response, (str, SearchResponse)):
        for chunk in response:
            print(chunk, end="", flush=True)
