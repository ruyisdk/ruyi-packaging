"""
This file is a set of data, records upstreams of manifests
"""

board_images: dict = {
    "armbian": {
        "data": {
            "source": "github",
            "github": "armbian/community",
            "use_latest_release": True,
        },
        "category": "board-image",
        "combos": ["armbian-pine64-star64", ],
    },
    "duo-buildroot-sdk": {
        "data": {
            "source": "github",
            "github": "milkv-duo/duo-buildroot-sdk",
            "use_latest_release": True,
        },
        "category": "board-image",
        "combos": ["arduino-milkv-duo-sd", "arduino-milkv-duo256m-sd", ],
    },
    "duo-buildroot-sdk-v2": {
        "data": {
            "source": "github",
            "github": "milkv-duo/duo-buildroot-sdk-v2",
            "use_latest_release": True,
        },
        "category": "board-image",
        "combos": ["buildroot-sdk-milkv-duo", "buildroot-sdk-milkv-duo256m", "buildroot-sdk-milkv-duos-sd",
                   "buildroot-sdk-milkv-duo256m-python", "buildroot-sdk-milkv-duo-python", ],
        "match": {
            "buildroot-sdk-milkv-duo256m-python": "",
            "buildroot-sdk-milkv-duo-python": "",
        },
    },
    "mars-buildroot-sdk": {
        "data": {
            "source": "github",
            "github": "milkv-mars/mars-buildroot-sdk",
            "use_latest_release": True,
        },
        "category": "board-image",
        "combos": ["debian-desktop-sdk-milkv-mars-sd", "debian-desktop-sdk-milkv-mars-cm-sd", ],
    },
    "LicheeRV-Nano-Build": {
        "data": {
            "source": "github",
            "github": "sipeed/LicheeRV-Nano-Build",
            "use_latest_release": True,
        },
        "category": "board-image",
        "combos": ["buildroot-sdk-sipeed-licheervnano", ],
    },
    "sophgo-sg200x-debian": {
        "data": {
            "source": "github",
            "github": "Fishwaldo/sophgo-sg200x-debian",
            "use_latest_release": True,
        },
        "category": "board-image",
        "combos": ["debian-fishwaldo-sg200x-sipeed-licheervnano", ],
    },
}
