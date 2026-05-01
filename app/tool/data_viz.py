from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

from app.config import Config
from app.logger import logger
from app.schema import ToolResult
from app.tool.base import BaseTool


class DataVisualization(BaseTool):
    name = "data_viz"
    description = (
        "Generate charts from data. Uses matplotlib (Python) to create PNG or HTML charts. "
        "Saves output to workspace/."
    )
    parameters = {
        "type": "object",
        "properties": {
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "scatter", "pie", "histogram"],
                "description": "Type of chart to generate.",
            },
            "data": {
                "type": "object",
                "description": "Chart data: {labels: [...], values: [...], title: '...'}",
            },
            "output_name": {
                "type": "string",
                "description": "Output filename (without extension). Saved to workspace/.",
                "default": "chart",
            },
            "format": {
                "type": "string",
                "enum": ["png", "html"],
                "default": "png",
                "description": "Output format.",
            },
        },
        "required": ["chart_type", "data"],
    }

    async def execute(
        self,
        chart_type: str,
        data: dict[str, Any],
        output_name: str = "chart",
        format: str = "png",
        **_: Any,
    ) -> ToolResult:
        workspace = Path(Config.get().workspace_dir)
        workspace.mkdir(exist_ok=True)
        out_path = workspace / f"{output_name}.{format}"

        labels = data.get("labels", [])
        values = data.get("values", [])
        title = data.get("title", chart_type.capitalize() + " Chart")

        code = self._build_matplotlib_code(chart_type, labels, values, title, str(out_path), format)
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return ToolResult(error=f"Chart generation failed: {result.stderr}")
            return ToolResult(output=f"Chart saved to {out_path}")
        except Exception as e:
            return ToolResult(error=str(e))

    def _build_matplotlib_code(
        self,
        chart_type: str,
        labels: list,
        values: list,
        title: str,
        out_path: str,
        fmt: str,
    ) -> str:
        labels_json = json.dumps(labels)
        values_json = json.dumps(values)
        return f"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

labels = {labels_json}
values = {values_json}
title = {json.dumps(title)}
out_path = {json.dumps(out_path)}
fmt = {json.dumps(fmt)}

fig, ax = plt.subplots(figsize=(10, 6))
if "{chart_type}" == "bar":
    ax.bar(labels, values)
elif "{chart_type}" == "line":
    ax.plot(labels, values, marker='o')
elif "{chart_type}" == "scatter":
    ax.scatter(labels, values)
elif "{chart_type}" == "pie":
    ax.pie(values, labels=labels, autopct='%1.1f%%')
elif "{chart_type}" == "histogram":
    ax.hist(values, bins=20)

ax.set_title(title)
plt.tight_layout()
if fmt == "html":
    import mpld3
    html = mpld3.fig_to_html(fig)
    with open(out_path, 'w') as f:
        f.write(html)
else:
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved to {{out_path}}")
"""
