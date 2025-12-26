"""
Generated VarModel from AIMD.
"""

from airalogy.types import AiralogyMarkdown, FileIdDOCX, FileIdPDF
from pydantic import BaseModel, Field


class VarModel(BaseModel):
    """Main variable model."""
    docx_file_id: FileIdDOCX = Field(description="Upload a .docx file")
    docx_source_filename: str = Field(description="Resolved source filename for the DOCX conversion")
    docx_markdown_text: AiralogyMarkdown = Field(description="Converted Markdown content for the DOCX document")
    docx_warnings: list[str] = Field(description="Non-fatal DOCX conversion warnings, if any")
    pdf_file_id: FileIdPDF = Field(description="Upload a .pdf file")
    pdf_source_filename: str = Field(description="Resolved source filename for the PDF conversion")
    pdf_markdown_text: AiralogyMarkdown = Field(description="Converted Markdown content for the PDF document")
    pdf_warnings: list[str] = Field(description="Non-fatal PDF conversion warnings, if any")