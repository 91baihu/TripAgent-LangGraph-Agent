"""导出路由 — 行程多格式下载 & 一键复制"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from ..auth import get_current_user
from ..database import get_db
from ..models import Trip
from ..services.export_service import ExportService

router = APIRouter()


async def _get_trip_or_404(db: AsyncSession, trip_id: str, user_id: str) -> Trip:
    """查询行程，不存在或无权访问时抛出 404"""
    from sqlalchemy import select

    stmt = select(Trip).where(Trip.id == trip_id, Trip.user_id == user_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    return trip


# ========== 文件下载导出 ==========
@router.get("/trips/{trip_id}/export")
async def export_trip(
    trip_id: str,
    format: str = Query(..., pattern="^(md|pdf|docx|txt|html)$", description="导出格式"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """下载导出文件

    支持的格式：
    - md: Markdown 文件
    - pdf: PDF 文档（需要 weasyprint，否则返回 HTML）
    - docx: Word 文档
    - txt: 纯文本文件
    - html: 网页文件

    Example:
        GET /api/v1/trips/{trip_id}/export?format=pdf
    """
    trip = await _get_trip_or_404(db, trip_id, current_user["sub"])
    exporter = ExportService(trip)

    # 格式 → 导出方法映射
    generators = {
        "md": exporter.to_markdown,
        "html": lambda: exporter.to_html().encode("utf-8"),
        "pdf": exporter.to_pdf,
        "docx": exporter.to_docx,
        "txt": exporter.to_plain_text().encode,
    }

    if format not in generators:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")

    content = generators[format]()
    mime_type = exporter.get_mime_type(format)
    filename = exporter.get_filename(format)

    # 记录已导出格式（阶段一新增字段）
    current_formats = trip.export_formats or []
    if format not in current_formats:
        current_formats.append(format)
        trip.export_formats = current_formats
        await db.commit()

    return StreamingResponse(
        BytesIO(content),
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )


# ========== 一键复制纯文本 ==========
@router.get("/trips/{trip_id}/export/text")
async def export_text_for_copy(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """返回纯文本内容，供前端一键复制到剪贴板

    返回 JSON 格式：{"text": "格式化纯文本内容"}
    前端使用 navigator.clipboard.writeText() 写入剪贴板。

    Example:
        GET /api/v1/trips/{trip_id}/export/text
    """
    trip = await _get_trip_or_404(db, trip_id, current_user["sub"])
    exporter = ExportService(trip)
    return {"text": exporter.to_plain_text(), "title": trip.title}


# ========== 导出预览 ==========
@router.get("/trips/{trip_id}/export/preview")
async def export_preview(
    trip_id: str,
    format: str = Query("html", pattern="^(html|md)$", description="预览格式"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """返回 Markdown 或 HTML 预览内容（在浏览器中渲染）

    Example:
        GET /api/v1/trips/{trip_id}/export/preview?format=html
    """
    trip = await _get_trip_or_404(db, trip_id, current_user["sub"])
    exporter = ExportService(trip)

    if format == "html":
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=exporter.to_html())

    # Markdown 预览
    return {"markdown": exporter.md_content, "title": trip.title}
