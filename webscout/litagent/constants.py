"""Constants used by the LitAgent module."""
from typing import Any

# Browser versions we support
BROWSERS = {
    "chrome": (100, 131),
    "firefox": (100, 132),
    "safari": (605, 619),
    "edge": (100, 131),
    "opera": (80, 114),
    "brave": (100, 131),
    "vivaldi": (5, 7)
}

# OS versions
OS_VERSIONS = {
    "windows": ["10.0", "11.0"],
    "mac": ["10_15_7", "11_0", "12_0", "13_0", "14_0", "15_0"],
    "linux": ["x86_64", "i686", "aarch64"],
    "android": ["10", "11", "12", "13", "14", "15"],
    "ios": ["14_0", "15_0", "16_0", "17_0", "18_0"],
    "chrome_os": ["14.0", "15.0", "16.0"]
}

# Device types
DEVICES = {
    "mobile": [
        "iPhone", "iPad", "Samsung Galaxy", "Google Pixel",
        "OnePlus", "Xiaomi", "Huawei", "OPPO", "Vivo"
    ],
    "desktop": ["Windows PC", "MacBook", "iMac", "Linux Desktop"],
    "tablet": ["iPad", "Samsung Galaxy Tab", "Microsoft Surface", "Huawei MatePad", "Lenovo Tab"],
    "console": ["PlayStation 5", "Xbox Series X", "Nintendo Switch", "PlayStation 4", "Xbox One"],
    "tv": ["Samsung Smart TV", "LG WebOS", "Android TV", "Apple TV", "Sony Bravia"],
    "wearable": ["Apple Watch", "Samsung Galaxy Watch", "Fitbit", "Garmin"]
}

# Browser fingerprinting components
FINGERPRINTS: dict[str, Any] = {
    "accept_language": [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.8,en-US;q=0.6",
        "es-ES,es;q=0.9,en;q=0.8",
        "fr-FR,fr;q=0.9,en;q=0.8",
        "de-DE,de;q=0.9,en;q=0.8"
    ],
    "accept": [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ],
    "sec_ch_ua": {
        "chrome": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"{}\", \"Google Chrome\";v=\"{}\"",
        "edge": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"{}\", \"Microsoft Edge\";v=\"{}\"",
        "firefox": "\"Firefox\";v=\"{}\", \"Not;A=Brand\";v=\"8\"",
        "safari": "\"Safari\";v=\"{}\", \"Not;A=Brand\";v=\"99\""
    },
    "platforms": [
        "Windows", "macOS", "Linux", "Android", "iOS"
    ]
}
