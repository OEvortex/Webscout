import sys
import urllib.parse
from typing import Any, Dict, Generator, Iterator, List, Optional, TypedDict, Union, cast
from uuid import uuid4

import cloudscraper
import requests

from webscout import exceptions
from webscout.AIbase import AISearch, SearchResponse
from webscout.litagent import LitAgent
from webscout.sanitize import sanitize_stream


class SourceDict(TypedDict, total=False):
    url: str
    title: str
    snippet: str
    favicon: str

class StatusUpdateDict(TypedDict, total=False):
    type: str
    message: str
    data: Any

class StatusTopBarDict(TypedDict, total=False):
    type: str
    data: dict

class PeopleAlsoAskDict(TypedDict, total=False):
    question: str
    answer: str

class ResultSummaryDict(TypedDict, total=False):
    source: str
    rel_score: float
    score: float
    llm_id: str
    cogen_name: str
    ended: bool

class Genspark(AISearch):
    """
    Strongly typed Genspark AI search API client.

    Updated to handle Unicode more gracefully and support more result fields.
    """

    session: cloudscraper.CloudScraper
    max_tokens: int
    chat_endpoint: str
    stream_chunk_size: int
    timeout: int
    log_raw_events: bool
    headers: Dict[str, str]
    cookies: Dict[str, str]
    last_response: Union[SearchResponse, str, List[Any], None] # type: ignore[assignment]
    search_query_details: Dict[str, Any]
    status_updates: List[StatusUpdateDict]
    final_search_results: Optional[List[Any]]
    sources_used: List[SourceDict]
    _seen_source_urls: set
    people_also_ask: List[PeopleAlsoAskDict]
    _seen_paa_questions: set
    agents_guide: Optional[List[Any]]
    result_summary: Dict[str, ResultSummaryDict]
    raw_events_log: List[dict]

    def __init__(
        self,
        timeout: int = 30,
        proxies: Optional[Dict[str, str]] = None,
        max_tokens: int = 600,
        log_raw_events: bool = False,
    ) -> None:
        self.session = cloudscraper.create_scraper()
        self.max_tokens = max_tokens
        self.chat_endpoint = "https://www.genspark.ai/api/search/stream"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.log_raw_events = log_raw_events
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://www.genspark.ai",
            "Priority": "u=1, i",
            "Sec-CH-UA": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "User-Agent": LitAgent().random(),
        }
        self.cookies = {
            "i18n_redirected": "en-US",
            "agree_terms": "0",
            "session_id": uuid4().hex,
        }
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        self.last_response = None
        self._reset_search_data()

    def _reset_search_data(self) -> None:
        """Resets attributes that store data from a search stream."""
        self.search_query_details = {}
        self.status_updates = []
        self.final_search_results = None
        self.sources_used = []
        self._seen_source_urls = set()
        self.people_also_ask = []
        self._seen_paa_questions = set()
        self.agents_guide = None
        self.result_summary = {}
        self.raw_events_log = []

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None], List[Any], Dict[str, Any], str]:
        """
        Strongly typed search method for Genspark API.

        Args:
            prompt: The search query or prompt.
            stream: If True, yields results as they arrive.
            raw: If True, yields/returns raw event dicts. If False, ONLY returns the actual AI text response.
            **kwargs: Additional parameters.
        """
        self._reset_search_data()
        url = f"{self.chat_endpoint}?query={urllib.parse.quote(prompt)}"

        def _process_stream() -> Generator[Union[Dict[str, str], SearchResponse], None, None]:
            CloudflareException = cloudscraper.exceptions.CloudflareException
            RequestException = requests.exceptions.RequestException
            try:
                with self.session.post(
                    url,
                    headers=self.headers,
                    cookies=self.cookies,
                    json={},
                    stream=True,
                    timeout=self.timeout,
                ) as resp:
                    if not resp.ok:
                        raise exceptions.APIConnectionError(
                            f"Failed to generate SearchResponse - ({resp.status_code}, {resp.reason}) - {resp.text}"
                        )
                def _extract_genspark_content(data: Union[str, Dict[str, Any]]) -> Optional[str]:
                    if isinstance(data, str):
                        return None
                    
                    event_type = data.get("type")
                    field_name = data.get("field_name")
                    result_id = data.get("result_id")

                    # Internal State Updates
                    if event_type == "result_start" and isinstance(result_id, str):
                        self.result_summary[result_id] = cast(ResultSummaryDict, {
                            "source": data.get("result_source"),
                            "rel_score": data.get("result_rel_score"),
                            "score": data.get("result_score"),
                            "llm_id": data.get("llm_id"),
                            "cogen_name": data.get("cogen", {}).get("name"),
                        })
                    elif event_type == "classify_query_result":
                        self.search_query_details["classification"] = data.get("classify_query_result")
                    elif event_type == "result_field":
                        field_value = data.get("field_value")
                        if field_name == "search_query":
                            self.search_query_details["query_string"] = field_value
                        elif field_name == "thinking":
                            self.status_updates.append({"type": "thinking", "message": str(field_value)})
                        elif field_name == "search_status_top_bar_data":
                            self.status_updates.append({"type": "status_top_bar", "data": field_value})
                            if isinstance(field_value, dict) and field_value.get("status") == "finished":
                                self.final_search_results = field_value.get("search_results")
                                if field_value.get("search_plan"):
                                    self.search_query_details["search_plan"] = field_value.get("search_plan")
                        elif field_name == "search_source_top_bar_data":
                            if isinstance(field_value, list):
                                for source in field_value:
                                    if isinstance(source, dict) and source.get("url") and source.get("url") not in self._seen_source_urls:
                                        self.sources_used.append(cast(SourceDict, source))
                                        self._seen_source_urls.add(source.get("url") )
                    elif event_type == "result_end":
                        if result_id in self.result_summary:
                            self.result_summary[result_id]["ended"] = True
                        search_result_data = data.get("search_result")
                        if search_result_data and isinstance(search_result_data, dict):
                            if search_result_data.get("source") == "people_also_ask" and "people_also_ask" in search_result_data:
                                paa_list = search_result_data["people_also_ask"]
                                if isinstance(paa_list, list):
                                    for paa_item in paa_list:
                                        if isinstance(paa_item, dict) and paa_item.get("question") not in self._seen_paa_questions:
                                            self.people_also_ask.append(cast(PeopleAlsoAskDict, paa_item))
                                            self._seen_paa_questions.add(paa_item.get("question") )
                            elif search_result_data.get("source") == "agents_guide" and "agents_guide" in search_result_data:
                                self.agents_guide = search_result_data["agents_guide"]

                    # Content extraction
                    if event_type == "result_field_delta" and field_name:
                        if (
                            field_name.startswith("streaming_detail_answer") or
                            field_name.startswith("streaming_simple_answer") or
                            field_name == "answer" or
                            field_name == "content"
                        ):
                            return data.get("delta", "")
                    return None

                processed_stream = sanitize_stream(
                    data=resp.iter_content(chunk_size=self.stream_chunk_size),
                    to_json=True,
                    extract_regexes=[r"data:\s*({.*})"],
                    content_extractor=lambda chunk: _extract_genspark_content(chunk),
                    yield_raw_on_error=False,
                    line_delimiter="\n",
                    raw=raw,
                    output_formatter=None if raw else lambda x: SearchResponse(x) if isinstance(x, str) else x,
                )

                for item in processed_stream:
                    yield item
            except CloudflareException as e:
                raise exceptions.APIConnectionError(f"Request failed due to Cloudscraper issue: {e}")
            except RequestException as e:
                raise exceptions.APIConnectionError(f"Request failed: {e}")

        processed_stream_gen = _process_stream()

        if stream:
            return processed_stream_gen
        else:
            full_SearchResponse_text = ""
            all_raw_events_for_this_search: List[dict] = []
            for item in processed_stream_gen:
                if raw:
                    all_raw_events_for_this_search.append(cast(dict, item))
                else:
                    if isinstance(item, SearchResponse):
                        full_SearchResponse_text += str(item)

            if raw:
                full_raw = "".join(str(item) for item in all_raw_events_for_this_search)
                self.last_response = full_raw
                return full_raw
            else:
                # Basic Unicode sanitization for the final response
                final_text_response = SearchResponse(full_SearchResponse_text)
                self.last_response = final_text_response
                return final_text_response

if __name__ == "__main__":
    ai = Genspark()
    try:
        search_result_stream = ai.search("liger-kernal details", stream=True, raw=False)

        if hasattr(search_result_stream, "__iter__") and not isinstance(search_result_stream, (str, bytes, SearchResponse)):
            for chunk in search_result_stream:
                try:
                    # Use a more robust way to print Unicode characters on Windows
                    text = str(chunk)
                    sys.stdout.write(text)
                    sys.stdout.flush()
                except UnicodeEncodeError:
                    # Fallback for Windows consoles that don't support UTF-8
                    safe_chunk = str(chunk).encode('ascii', errors='replace').decode('ascii')
                    sys.stdout.write(safe_chunk)
                    sys.stdout.flush()
        else:
            print(search_result_stream)
        print()

    except KeyboardInterrupt:
        print("\nSearch interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
