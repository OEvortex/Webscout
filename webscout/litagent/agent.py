"""
LitAgent: Advanced User Agent Generation and Management System.

This module provides a robust and flexible system for generating realistic,
modern user agents and managing browser fingerprints for web scraping and
automation purposes.
"""

import json
import random
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from webscout.litagent.constants import BROWSERS, DEVICES, FINGERPRINTS, OS_VERSIONS


class LitAgent:
    """
    A powerful and modern user agent generator for web scraping and automation.

    LitAgent provides tools for generating randomized but realistic user agent strings,
    managing proxy pools, rotating IPs, and simulating browser fingerprints to avoid
    detection and rate limiting.
    """

    _blacklist: Set[str]
    _whitelist: Set[str]
    _agents: List[str]
    _ip_pool: List[str]
    _ip_index: int
    _proxy_pool: List[str]
    _proxy_index: int
    _history: List[str]
    _refresh_timer: Optional[threading.Timer]
    _stats: Dict[str, Any]
    thread_safe: bool
    lock: Optional[threading.RLock]

    @property
    def agents(self) -> List[str]:
        """Returns the current pool of user agents."""
        return self._agents

    @property
    def ip_pool(self) -> List[str]:
        """Returns the current simulated IP pool."""
        return self._ip_pool

    def __init__(self, thread_safe: bool = False):
        """
        Initialize the LitAgent instance.

        Args:
            thread_safe (bool): If True, use RLock for thread-safe operations.
        """
        self.thread_safe = thread_safe
        self.lock = threading.RLock() if thread_safe else None

        # Internal state
        self._blacklist: Set[str] = set()
        self._whitelist: Set[str] = set()
        self._agents: List[str] = self._generate_agents(100)
        self._ip_pool: List[str] = self._generate_ip_pool(20)
        self._ip_index: int = 0
        self._proxy_pool: List[str] = []
        self._proxy_index: int = 0
        self._history: List[str] = []
        self._refresh_timer: Optional[threading.Timer] = None

        # Usage statistics
        self._stats = {
            "total_generated": 100,
            "requests_served": 0,
            "browser_usage": {browser: 0 for browser in BROWSERS.keys()},
            "device_usage": {device: 0 for device in DEVICES.keys()},
            "start_time": datetime.now().isoformat()
        }

    def _generate_agents(self, count: int) -> List[str]:
        """
        Generate a list of realistic user agent strings.

        Args:
            count (int): Number of agents to generate.

        Returns:
            List[str]: A list of generated user agent strings.
        """
        agents: List[str] = []
        for _ in range(count):
            agent = ""
            browser: str = random.choice(list(BROWSERS.keys()))
            version_range: Tuple[int, int] = BROWSERS.get(browser, (100, 130))
            version: int = random.randint(*version_range)

            if browser in ['chrome', 'firefox', 'edge', 'opera', 'brave', 'vivaldi']:
                os_type: str = random.choice(['windows', 'mac', 'linux'])
                os_ver: str = random.choice(OS_VERSIONS.get(os_type, ["10.0"]))

                if os_type == 'windows':
                    platform = f"Windows NT {os_ver}; Win64; x64"
                elif os_type == 'mac':
                    platform = f"Macintosh; Intel Mac OS X {os_ver}"
                else:
                    platform = f"X11; Linux {os_ver}"

                agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) "

                if browser == 'chrome':
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36"
                elif browser == 'firefox':
                    agent += f"Firefox/{version}.0"
                elif browser == 'edge':
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36 Edg/{version}.0.0.0"
                elif browser == 'opera':
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36 OPR/{version}.0.0.0"
                elif browser == 'brave':
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36 Brave/{version}.0.0.0"
                elif browser == 'vivaldi':
                    vivaldi_build: int = random.randint(1000, 9999)
                    agent += f"Chrome/{version}.0.0.0 Safari/537.36 Vivaldi/{version}.0.{vivaldi_build}"

            elif browser == 'safari':
                device: str = random.choice(['mac', 'ios'])
                if device == 'mac':
                    ver: str = random.choice(OS_VERSIONS.get('mac', ["10_15_7"]))
                    agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X {ver}) "
                else:
                    ver = random.choice(OS_VERSIONS.get('ios', ["17_0"]))
                    device_name: str = random.choice(['iPhone', 'iPad'])
                    agent = f"Mozilla/5.0 ({device_name}; CPU OS {ver} like Mac OS X) "

                agent += f"AppleWebKit/{version}.1.15 (KHTML, like Gecko) Version/{version//10}.0 Safari/{version}.1.15"

            agents.append(agent)

        # Ensure uniqueness and respects current whitelist/blacklist
        unique_agents = list(set(agents))
        return [a for a in unique_agents if a not in self._blacklist]

    def _update_stats(self, browser_type: Optional[str] = None, device_type: Optional[str] = None) -> None:
        """Update internal usage statistics."""
        def update() -> None:
            self._stats["requests_served"] += 1
            if browser_type:
                self._stats["browser_usage"][browser_type] = self._stats["browser_usage"].get(browser_type, 0) + 1
            if device_type:
                self._stats["device_usage"][device_type] = self._stats["device_usage"].get(device_type, 0) + 1

        if self.thread_safe and self.lock:
            with self.lock:
                update()
        else:
            update()

    def _add_to_history(self, agent: str) -> None:
        """Add a generated agent to history."""
        def add() -> None:
            self._history.append(agent)
            if len(self._history) > 50:
                self._history.pop(0)

        if self.thread_safe and self.lock:
            with self.lock:
                add()
        else:
            add()

    def random(self) -> str:
        """
        Get a random user agent from the pool.

        Returns:
            str: A random user agent string.
        """
        pool = list(self._whitelist) if self._whitelist else self._agents
        if not pool:
            # Fallback if somehow empty
            pool = self._generate_agents(1)

        agent = random.choice(pool)
        self._update_stats()
        self._add_to_history(agent)
        return agent

    def browser(self, name: str) -> str:
        """
        Get a user agent for a specific browser.

        Args:
            name (str): Browser name (e.g., 'chrome', 'firefox').

        Returns:
            str: A browser-specific user agent string.
        """
        name = name.lower()
        if name not in BROWSERS:
            return self.random()

        matching_agents = [a for a in self._agents if name in a.lower()]
        if not matching_agents:
            # Generate one on the fly if needed
            matched = self.custom(browser=name)
        else:
            matched = random.choice(matching_agents)

        self._update_stats(browser_type=name)
        self._add_to_history(matched)
        return matched

    def mobile(self) -> str:
        """Returns a mobile device user agent."""
        matching = [a for a in self._agents if any(d in a for d in DEVICES.get('mobile', []))]
        agent = random.choice(matching) if matching else self.custom(device_type="mobile")
        self._update_stats(device_type="mobile")
        return agent

    def desktop(self) -> str:
        """Returns a desktop device user agent."""
        matching = [a for a in self._agents if any(d in a for d in ["Windows", "Macintosh", "X11"])]
        agent = random.choice(matching) if matching else self.custom(device_type="desktop")
        self._update_stats(device_type="desktop")
        return agent

    def tablet(self) -> str:
        """Returns a tablet device user agent."""
        matching = [a for a in self._agents if 'iPad' in a or ('Android' in a and 'Mobile' not in a)]
        agent = random.choice(matching) if matching else self.custom(device_type="tablet")
        self._update_stats(device_type="tablet")
        return agent

    def chrome(self) -> str: return self.browser('chrome')
    def firefox(self) -> str: return self.browser('firefox')
    def safari(self) -> str: return self.browser('safari')
    def edge(self) -> str: return self.browser('edge')
    def opera(self) -> str: return self.browser('opera')
    def brave(self) -> str: return self.browser('brave')
    def vivaldi(self) -> str: return self.browser('vivaldi')

    def windows(self) -> str: return self.custom(os='windows')
    def macos(self) -> str: return self.custom(os='mac')
    def linux(self) -> str: return self.custom(os='linux')
    def android(self) -> str: return self.custom(os='android')
    def ios(self) -> str: return self.custom(os='ios')

    def custom(self, browser: Optional[str] = None, version: Optional[str] = None,
               os: Optional[str] = None, os_version: Optional[str] = None,
               device_type: Optional[str] = None) -> str:
        """
        Generate a customized user agent string.

        Args:
            browser (str, optional): Browser name.
            version (str, optional): Browser version.
            os (str, optional): Operating system.
            os_version (str, optional): OS version.
            device_type (str, optional): Device type ('desktop', 'mobile', 'tablet').

        Returns:
            str: The customized user agent string.
        """
        browser = browser.lower() if browser else 'chrome'
        v_range = BROWSERS.get(browser, (100, 130))
        v_num = int(version.split('.')[0]) if version else random.randint(*v_range)

        os = os.lower() if os else random.choice(['windows', 'mac', 'linux'])
        os_ver = os_version or random.choice(OS_VERSIONS.get(os, ["10.0"]))
        device_type = (device_type or 'desktop').lower()

        if os == 'windows':
            platform = f"Windows NT {os_ver}; Win64; x64"
        elif os == 'mac':
            platform = f"Macintosh; Intel Mac OS X {os_ver}"
        elif os == 'linux':
            platform = f"X11; Linux {os_ver}"
        elif os == 'android':
            platform = f"Linux; Android {os_ver}; {random.choice(DEVICES.get('mobile', ['Samsung Galaxy']))}"
        elif os == 'ios':
            dev = 'iPhone' if device_type == 'mobile' else 'iPad'
            platform = f"{dev}; CPU OS {os_ver} like Mac OS X"
        else:
            platform = "Windows NT 10.0; Win64; x64"

        agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) "

        if browser == 'chrome':
            agent += f"Chrome/{v_num}.0.0.0 Safari/537.36"
        elif browser == 'firefox':
            agent += f"Firefox/{v_num}.0"
        elif browser == 'safari':
            agent += f"Version/{v_num//10}.0 Safari/{v_num}.1.15"
        elif browser == 'edge':
            agent += f"Chrome/{v_num}.0.0.0 Safari/537.36 Edg/{v_num}.0.0.0"
        else:
            agent += f"Chrome/{v_num}.0.0.0 Safari/537.36"

        self._update_stats(browser_type=browser, device_type=device_type)
        return agent

    def generate_fingerprint(self, browser: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a complete browser fingerprint.

        Args:
            browser (str, optional): Requested browser type.

        Returns:
            Dict[str, str]: A dictionary containing headers and fingerprint data.
        """
        ua = self.browser(browser) if browser else self.random()
        ip = self.rotate_ip()

        sec_ch_ua = ""
        sec_ch_ua_dict = cast(Dict[str, str], FINGERPRINTS.get("sec_ch_ua", {}))
        for b_name in sec_ch_ua_dict:
            if b_name in ua.lower():
                v = random.randint(*BROWSERS.get(b_name, (100, 120)))
                sec_ch_ua = sec_ch_ua_dict[b_name].format(v, v)
                break

        accept_language_list = cast(List[str], FINGERPRINTS.get("accept_language", ["en-US,en;q=0.9"]))
        accept_list = cast(List[str], FINGERPRINTS.get("accept", ["*/*"]))
        platforms_list = cast(List[str], FINGERPRINTS.get("platforms", ["Windows"]))

        return {
            "user_agent": ua,
            "accept_language": random.choice(accept_language_list),
            "accept": random.choice(accept_list),
            "sec_ch_ua": sec_ch_ua,
            "platform": random.choice(platforms_list),
            "x-forwarded-for": ip,
            "x-real-ip": ip,
            "x-client-ip": ip,
            "forwarded": f"for={ip};proto=https",
            "x-request-id": self.random_id(8),
        }

    def smart_tv(self) -> str:
        """Generate a Smart TV user agent."""
        tv: str = random.choice(DEVICES.get('tv', ["Samsung Smart TV"]))
        if 'Samsung' in tv:
            agent: str = f"Mozilla/5.0 (SMART-TV; SAMSUNG; {tv}; Tizen 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        elif 'LG' in tv:
            agent = f"Mozilla/5.0 (Web0S; {tv}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
        else:
            agent = f"Mozilla/5.0 (Linux; {tv}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"

        self._update_stats(device_type="tv")
        return agent

    def gaming(self) -> str:
        """Generate a gaming console user agent."""
        console: str = random.choice(DEVICES.get('console', ["PlayStation 5"]))
        if 'PlayStation' in console:
            agent: str = f"Mozilla/5.0 ({console}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15"
        elif 'Xbox' in console:
            agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; Xbox; {console}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edge/110.0.1587.41"
        else:
            agent = self.random()

        self._update_stats(device_type="console")
        return agent

    def wearable(self) -> str:
        """Generate a wearable device user agent."""
        dev: str = random.choice(DEVICES.get('wearable', ["Apple Watch"]))
        if 'Apple Watch' in dev:
            agent: str = "Mozilla/5.0 (AppleWatch; CPU WatchOS like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/10.0 Mobile/15E148 Safari/605.1"
        else:
            agent = f"Mozilla/5.0 (Linux; {dev}) AppleWebKit/537.36 (KHTML, like Gecko)"

        self._update_stats(device_type="wearable")
        return agent

    def refresh(self) -> None:
        """Refresh the internal agents pool with new values."""
        def do_refresh() -> None:
            self._agents = self._generate_agents(100)
            self._stats["total_generated"] += 100

        if self.thread_safe and self.lock:
            with self.lock:
                do_refresh()
        else:
            do_refresh()

    def auto_refresh(self, interval_minutes: int = 30) -> None:
        """
        Schedule automatic background refreshing of the agents pool.

        Args:
            interval_minutes (int): Time between refreshes in minutes.
        """
        if self._refresh_timer:
            self._refresh_timer.cancel()

        def _task() -> None:
            self.refresh()
            self._refresh_timer = threading.Timer(interval_minutes * 60, _task)
            self._refresh_timer.daemon = True
            self._refresh_timer.start()

        self._refresh_timer = threading.Timer(interval_minutes * 60, _task)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

    def rotate_ip(self) -> str:
        """Rotate through the IP pool and returns the next IP address."""
        def rot() -> str:
            ip: str = self._ip_pool[self._ip_index]
            self._ip_index = (self._ip_index + 1) % len(self._ip_pool)
            return ip

        if self.thread_safe and self.lock:
            with self.lock:
                return rot()
        return rot()

    def set_proxy_pool(self, proxies: List[str]) -> None:
        """Set a pool of proxies for rotation."""
        self._proxy_pool = proxies
        self._proxy_index = 0

    def rotate_proxy(self) -> Optional[str]:
        """Rotate through and return the next proxy from the pool."""
        if not self._proxy_pool:
            return None

        def rot() -> str:
            proxy: str = self._proxy_pool[self._proxy_index]
            self._proxy_index = (self._proxy_index + 1) % len(self._proxy_pool)
            return proxy

        if self.thread_safe and self.lock:
            with self.lock:
                return rot()
        return rot()

    def add_to_blacklist(self, agent: str) -> None:
        """Blacklist a specific user agent string."""
        self._blacklist.add(agent)
        if agent in self._agents:
            self._agents.remove(agent)

    def add_to_whitelist(self, agent: str) -> None:
        """Limit results to only those in the whitelist."""
        self._whitelist.add(agent)

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        stats = self._stats.copy()
        usage = stats["browser_usage"]
        stats["top_browser"] = max(usage.items(), key=lambda x: x[1])[0] if any(usage.values()) else None
        stats["avoidance_rate"] = min(99.9, 90 + (stats["total_generated"] / 1000))
        return stats

    def export_stats(self, filename: str) -> bool:
        """Export stats to a JSON file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.get_stats(), f, indent=4)
            return True
        except Exception:
            return False

    def validate_agent(self, agent: str) -> bool:
        """Perform basic validation on a user agent string."""
        return isinstance(agent, str) and agent.startswith("Mozilla/5.0")

    def random_id(self, length: int = 16) -> str:
        """Generate a random hexadecimal string ID."""
        return ''.join(random.choices('0123456789abcdef', k=length))

    def _generate_ip_pool(self, count: int) -> List[str]:
        """Generate a pool of random IP addresses."""
        return [".".join(str(random.randint(0, 255)) for _ in range(4)) for _ in range(count)]

    def __repr__(self) -> str:
        return f"<LitAgent(agents={len(self._agents)}, thread_safe={self.thread_safe})>"

    def __str__(self) -> str:
        return f"LitAgent Generator with {len(self._agents)} agents in pool"


if __name__ == "__main__":
    # Quick test
    agent = LitAgent()
    print(f"Random: {agent.random()}")
    print(f"Chrome: {agent.chrome()}")
    print(f"iPhone: {agent.ios()}")
    print(f"Fingerprint: {json.dumps(agent.generate_fingerprint(), indent=2)}")
