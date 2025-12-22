try:
    from ._build_info import VERSION as __version__
    from ._build_info import AUTHOR as __author__
except ImportError:
    __version__ = "Dev"
    __author__ = "Unknown"
