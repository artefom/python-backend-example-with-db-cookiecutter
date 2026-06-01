"""
Log related utils for tests
"""

import io
import json
from typing import Any, Dict, List


class JsonLogs(io.StringIO):
    def parse(self) -> List[Dict[str, Any]]:
        lines = list()
        for line in self.getvalue().splitlines():
            if not line:
                continue
            lines.append(json.loads(line))
        return lines
