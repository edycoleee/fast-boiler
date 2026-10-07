from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Iterable

from fastapi.responses import Response
from openpyxl import Workbook
from openpyxl.styles import Font


def excel_response(*, filename_prefix: str, sheet_name: str, headers: list[str], rows: Iterable[list[object]]) -> Response:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name[:31] or "Sheet1"
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    output = BytesIO()
    workbook.save(output)
    workbook.close()
    output.seek(0)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"{filename_prefix}-{stamp}.xlsx"
    headers_map = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers_map,
    )
