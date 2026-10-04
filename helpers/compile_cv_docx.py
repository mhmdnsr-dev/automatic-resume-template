"""Internal DOCX backend for the root compile_cv.py entry point.

The selected LaTeX file remains the sole content source. This module parses the
resume's semantic macros and maps them to an editable, ATS-friendly Word file.

Design system: compact_reference_guide with the named ``master_tex_match``
override. Margins and spacing stay compact, while font sizes mirror the LaTeX
11pt article scale using Word's half-point precision: Huge 25pt, large 12pt,
normalsize 11pt, small 10pt, and tiny 6pt. The first-page furniture is a
custom centered resume masthead.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

FONT = "Arial"
INK = RGBColor(0, 0, 0)
APP_PROPERTIES_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
VT_PROPERTIES_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"


@dataclass
class Entry:
    left: str
    right: str
    subtitle: str = ""
    location: str = ""
    bullets: list[str] = field(default_factory=list)
    items: list[tuple[str, str, str]] = field(default_factory=list)


@dataclass
class Resume:
    name: str
    location: str
    contacts: list[tuple[str, str]]
    summary: str
    experience: list[Entry]
    projects: list[Entry]
    education: list[Entry]
    skills: list[tuple[str, str]]


def _strip_comments(text: str) -> str:
    return re.sub(r"(?m)(?<!\\)%.*$", "", text)


def _read_group(text: str, start: int) -> tuple[str, int]:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        raise ValueError(f"Expected '{{' near character {start}")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{" and (i == 0 or text[i - 1] != "\\"):
            depth += 1
        elif text[i] == "}" and (i == 0 or text[i - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
    raise ValueError("Unclosed LaTeX group")


def _macro_calls(text: str, names: tuple[str, ...]) -> list[tuple[int, str, list[str]]]:
    pattern = re.compile(r"\\(" + "|".join(map(re.escape, names)) + r")\b")
    counts = {
        "resumeSubheading": 4,
        "resumeEmployerHeading": 4,
        "resumeEducationHeading": 4,
        "resumeSubSubheading": 2,
        "resumeRole": 2,
        "resumeProjectHeading": 2,
        "resumeItem": 1,
    }
    calls = []
    for match in pattern.finditer(text):
        pos = match.end()
        args = []
        try:
            for _ in range(counts[match.group(1)]):
                value, pos = _read_group(text, pos)
                args.append(value)
        except ValueError:
            continue
        calls.append((match.start(), match.group(1), args))
    return calls


def _href_calls(text: str) -> list[tuple[str, str]]:
    links = []
    for match in re.finditer(r"\\href\b", text):
        try:
            url, pos = _read_group(text, match.end())
            label, _ = _read_group(text, pos)
        except ValueError:
            continue
        links.append((url, label))
    return links


def _section(text: str, name: str, next_name: str | None) -> str:
    start_match = re.search(r"\\section\{" + re.escape(name) + r"\}", text)
    if not start_match:
        raise ValueError(f"Missing required section: {name}")
    end = len(text)
    if next_name:
        next_match = re.search(r"\\section\{" + re.escape(next_name) + r"\}", text[start_match.end() :])
        if next_match:
            end = start_match.end() + next_match.start()
    return text[start_match.end() : end]


def _latex_plain(value: str) -> str:
    value = value.replace(r"\textbar{}", "|").replace(r"\textbar", "|")
    value = re.sub(r"\\noatstext\{(?:[^{}]|\{[^{}]*\})*\}", "", value)
    value = re.sub(r"\\(?:vspace|hspace)\*?\{[^{}]*\}", "", value)
    value = re.sub(r"\\raisebox\{[^{}]*\}\{[^{}]*\}", "", value)
    previous = None
    while previous != value:
        previous = value
        value = re.sub(r"\\href\{([^{}]*)\}\{([^{}]*)\}", r"\2", value)
        value = re.sub(r"\\(?:textbf|textit|emph|underline|small|normalfont|scshape)\s*\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\(?:textbf|textit|emph|underline|small|normalfont|scshape)\b", "", value)
    value = re.sub(r"\\[A-Za-z@]+(?:\[[^\]]*\])?", "", value)
    replacements = {
        r"\&": "&", r"\%": "%", r"\_": "_", r"\#": "#",
        r"\$": "$", "~": " ", "---": " - ", "--": "\u2013", "$|$": "|",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = value.replace("{", "").replace("}", "").replace("$", "")
    return re.sub(r"\s+", " ", value).strip(" \\")


def _inline_segments(value: str) -> list[tuple[str, str, str]]:
    """Return ordered plain-text and hyperlink segments from inline LaTeX."""
    templated: list[str] = []
    links: dict[str, tuple[str, str]] = {}
    cursor = 0
    for index, match in enumerate(re.finditer(r"\\href\b", value)):
        if match.start() < cursor:
            continue
        try:
            url, pos = _read_group(value, match.end())
            label, end = _read_group(value, pos)
        except ValueError:
            continue
        token = f"CVLINKTOKEN{index}"
        templated.extend((value[cursor : match.start()], token))
        links[token] = (_latex_plain(label) or url, url)
        cursor = end
    templated.append(value[cursor:])

    plain = _latex_plain("".join(templated))
    if not links:
        return [("text", plain, "")] if plain else []

    token_pattern = "(" + "|".join(map(re.escape, links)) + ")"
    segments: list[tuple[str, str, str]] = []
    for part in re.split(token_pattern, plain):
        if not part:
            continue
        if part in links:
            label, url = links[part]
            segments.append(("link", label, url))
        else:
            segments.append(("text", part, ""))
    return segments


def _parse_entries(
    section: str,
    project: bool = False,
    heading_macros: tuple[str, ...] | None = None,
) -> list[Entry]:
    if project:
        entry_heading_macros = ("resumeProjectHeading",)
    else:
        entry_heading_macros = heading_macros or (
            "resumeSubheading",
            "resumeEmployerHeading",
        )
    calls = _macro_calls(
        section,
        entry_heading_macros + ("resumeSubSubheading", "resumeRole", "resumeItem"),
    )
    entries: list[Entry] = []
    current: Entry | None = None
    for _, name, args in calls:
        if name in entry_heading_macros:
            if project:
                current = Entry(_latex_plain(args[0]), _latex_plain(args[1]))
            else:
                current = Entry(*(_latex_plain(x) for x in args))
            entries.append(current)
        elif name in {"resumeSubSubheading", "resumeRole"} and current:
            current.items.append(("subheading", _latex_plain(args[0]), _latex_plain(args[1])))
        elif name == "resumeItem" and current:
            plain = _latex_plain(args[0])
            current.bullets.append(plain)
            current.items.append(("bullet", plain, args[0]))
    return entries


def parse_resume(tex_path: Path) -> Resume:
    text = _strip_comments(tex_path.read_text(encoding="utf-8"))
    document = text.split(r"\begin{document}", 1)[-1]
    name_match = None
    for pattern in (
        r"\\fontsize\{[^{}]+\}\{[^{}]+\}\\selectfont\\bfseries\s+([^}\\]+)",
        r"\\Huge\s+\\scshape\s+([^}\\]+)",
    ):
        name_match = re.search(pattern, document)
        if name_match:
            break
    name = _latex_plain(name_match.group(1)) if name_match else tex_path.stem

    location_match = None
    for pattern in (
        r"\\fontsize\{[^{}]+\}\{[^{}]+\}\\selectfont\\bfseries\s+[^}\\]+\}"
        r"\s*\\\\\[[^\]]+\]\s*\n\s*([^\\\n]+?)\s+\\enspace\|",
        r"\\endAccSupp\{\}\s*\n\}\s*\n\s*([^\\\n]+)\\\\",
        r"\}\s*\\\\\s*\\vspace\{[^}]+\}\s*\n\s*([^\\\n]+)\\\\",
    ):
        location_match = re.search(pattern, document)
        if location_match:
            break
    location = _latex_plain(location_match.group(1)) if location_match else ""

    header = document.split(r"\section{Professional Summary}", 1)[0]
    contacts = []
    for url, label in _href_calls(header):
        display = _latex_plain(label)
        if url.startswith("tel:"):
            display = url.removeprefix("tel:")
        elif url.startswith("mailto:"):
            display = url.removeprefix("mailto:")
        elif not display:
            display = re.sub(r"^https?://", "", url).rstrip("/")
        contacts.append((display, url))

    summary_section = _section(document, "Professional Summary", "Experience")
    summary_items = _macro_calls(summary_section, ("resumeItem",))
    if summary_items:
        summary = _latex_plain(summary_items[0][2][0])
    else:
        item_match = re.search(r"\\item\s+\\small\s*\{", summary_section)
        if item_match:
            raw, _ = _read_group(summary_section, item_match.end() - 1)
            summary = _latex_plain(raw)
        else:
            summary = _latex_plain(summary_section)

    skills_section = _section(document, "Technical Skills", None).split(
        r"\end{document}", 1
    )[0]
    skills = [
        (_latex_plain(label), _latex_plain(value).lstrip(": "))
        for label, value in re.findall(r"\\textbf\{([^{}]+)\}\s*\{([^{}]+)\}", skills_section)
    ]
    if not skills:
        for line in re.split(r"\\\\", skills_section):
            match = re.search(r"\\textbf\{([^{}]+):\}\s*(.+)", line, re.DOTALL)
            if match:
                skills.append(
                    (_latex_plain(match.group(1)), _latex_plain(match.group(2)))
                )
    return Resume(
        name=name,
        location=location,
        contacts=contacts,
        summary=summary,
        experience=_parse_entries(
            _section(document, "Experience", "Personal Projects"),
            heading_macros=("resumeSubheading", "resumeEmployerHeading"),
        ),
        projects=_parse_entries(_section(document, "Personal Projects", "Education"), project=True),
        education=_parse_entries(
            _section(document, "Education", "Technical Skills"),
            heading_macros=("resumeSubheading", "resumeEducationHeading"),
        ),
        skills=skills,
    )


def _set_font(run, size: float, bold: bool = False, italic: bool = False) -> None:
    run.font.name = FONT
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:ascii"), FONT)
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:hAnsi"), FONT)
    run.font.size = Pt(size)
    run.font.color.rgb = INK
    run.bold = bold
    run.italic = italic


def _add_hyperlink(paragraph, label: str, url: str, size: float = 10.0) -> None:
    rid = paragraph.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), rid)
    run = OxmlElement("w:r")
    props = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), FONT)
    fonts.set(qn("w:hAnsi"), FONT)
    color = OxmlElement("w:color"); color.set(qn("w:val"), "000000")
    underline = OxmlElement("w:u"); underline.set(qn("w:val"), "single")
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(round(size * 2)))
    props.extend((fonts, color, underline, sz))
    run.append(props)
    text = OxmlElement("w:t"); text.text = label
    run.append(text); hyperlink.append(run); paragraph._p.append(hyperlink)


def _keep(paragraph, next_paragraph: bool = False) -> None:
    props = paragraph._p.get_or_add_pPr()
    keep_lines = OxmlElement("w:keepLines")
    keep_next = OxmlElement("w:keepNext")
    if not next_paragraph:
        keep_next.set(qn("w:val"), "0")
    props.extend((keep_lines, keep_next))


def _section_heading(document: Document, title: str) -> None:
    paragraph = document.add_paragraph(style="Heading 1")
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(1)
    _set_font(paragraph.add_run(title), 12.0, bold=True)
    props = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for key, value in (("val", "single"), ("sz", "6"), ("space", "1"), ("color", "000000")):
        bottom.set(qn(f"w:{key}"), value)
    borders.append(bottom); props.append(borders); _keep(paragraph, True)


def _entry_heading(document: Document, entry: Entry, small_heading: bool = False) -> None:
    has_subtitle = bool(entry.subtitle or entry.location)
    has_items = bool(entry.items)
    paragraph = document.add_paragraph(style="Heading 2")
    paragraph.paragraph_format.tab_stops.add_tab_stop(Inches(7.25), WD_TAB_ALIGNMENT.RIGHT)
    paragraph.paragraph_format.space_before = Pt(.5)
    paragraph.paragraph_format.space_after = Pt(0)
    _set_font(paragraph.add_run(entry.left), 10.0 if small_heading else 11.0, bold=True)
    paragraph.add_run("\t")
    _set_font(paragraph.add_run(entry.right), 10.0, bold=True)
    _keep(paragraph, has_subtitle or has_items)
    if has_subtitle:
        paragraph = document.add_paragraph(style="Heading 3")
        paragraph.paragraph_format.tab_stops.add_tab_stop(Inches(7.25), WD_TAB_ALIGNMENT.RIGHT)
        paragraph.paragraph_format.space_after = Pt(0)
        _set_font(paragraph.add_run(entry.subtitle), 10.0, italic=True)
        paragraph.add_run("\t")
        _set_font(paragraph.add_run(entry.location), 10.0, italic=True)
        _keep(paragraph, has_items)


def _add_inline_content(paragraph, value: str, size: float = 10.0) -> None:
    for kind, text, url in _inline_segments(value):
        if kind == "link":
            _add_hyperlink(paragraph, text, url, size)
        else:
            _set_font(paragraph.add_run(text), size)


def _add_bullet(document: Document, text: str, raw_latex: str = "") -> None:
    paragraph = document.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.left_indent = Inches(.22)
    paragraph.paragraph_format.first_line_indent = Inches(-.14)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    if raw_latex:
        _add_inline_content(paragraph, raw_latex)
    else:
        _set_font(paragraph.add_run(text), 10.0)
    _keep(paragraph)


def _add_subheading(document: Document, left: str, right: str) -> None:
    paragraph = document.add_paragraph(style="Heading 3")
    paragraph.paragraph_format.left_indent = Inches(.1)
    paragraph.paragraph_format.tab_stops.add_tab_stop(Inches(7.15), WD_TAB_ALIGNMENT.RIGHT)
    paragraph.paragraph_format.space_before = Pt(.5)
    paragraph.paragraph_format.space_after = Pt(0)
    _set_font(paragraph.add_run(left), 10.0, bold=True, italic=True)
    paragraph.add_run("\t")
    _set_font(paragraph.add_run(right), 10.0, italic=True)
    _keep(paragraph, True)


def _render_items(document: Document, items: list[tuple[str, str, str]]) -> None:
    for kind, left, right in items:
        if kind == "subheading":
            _add_subheading(document, left, right)
        elif kind == "bullet":
            _add_bullet(document, left, right)


def _add_contact_row(
    document: Document,
    contacts: list[tuple[str, str]],
    prefix: str = "",
) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(0)
    if prefix:
        _set_font(paragraph.add_run(prefix), 10.0)
    for index, (label, url) in enumerate(contacts):
        if prefix or index:
            _set_font(paragraph.add_run(" | "), 10.0)
        _add_hyperlink(paragraph, label, url)


def build_document(resume: Resume) -> Document:
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.5); section.page_height = Inches(11)
    section.top_margin = Inches(.58); section.bottom_margin = Inches(.58)
    section.left_margin = Inches(.58); section.right_margin = Inches(.58)
    section.header_distance = Inches(.25); section.footer_distance = Inches(.25)

    for style_name in ("Normal", "Heading 1", "Heading 2", "Heading 3", "List Bullet"):
        style = document.styles[style_name]
        style.font.name = FONT
        style._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:ascii"), FONT)
        style._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:hAnsi"), FONT)
        style.font.color.rgb = INK
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.line_spacing = 1.0

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(0)
    _set_font(paragraph.add_run(resume.name.upper()), 24.0, bold=True)

    _add_contact_row(document, resume.contacts[:2], resume.location)
    _add_contact_row(document, resume.contacts[2:])

    _section_heading(document, "Professional Summary")
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(0)
    _set_font(paragraph.add_run(resume.summary), 10.0)

    _section_heading(document, "Experience")
    for entry in resume.experience:
        _entry_heading(document, entry)
        _render_items(document, entry.items)

    _section_heading(document, "Personal Projects")
    for entry in resume.projects:
        _entry_heading(document, entry, small_heading=True)
        _render_items(document, entry.items)

    _section_heading(document, "Education")
    for entry in resume.education:
        _entry_heading(document, entry)

    _section_heading(document, "Technical Skills")
    for label, value in resume.skills:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = Pt(10.5)
        _set_font(paragraph.add_run(f"{label}: "), 10.0, bold=True)
        _set_font(paragraph.add_run(value), 10.0)

    props = document.core_properties
    props.title = f"{resume.name} - Frontend Developer"
    props.author = resume.name
    props.subject = "Frontend Developer Resume - React and Angular"
    props.keywords = ", ".join(
        value.rstrip(".")
        for label, value in resume.skills
        if label in {"Languages", "Frontend"}
    )
    props.comments = "Example Candidate frontend resume generated from the canonical LaTeX source"
    props.last_modified_by = resume.name
    now = datetime.now(timezone.utc)
    props.created = now
    props.modified = now
    return document


def _resume_statistics(resume: Resume) -> tuple[int, int]:
    values = [resume.name, resume.location, resume.summary]
    values.extend(label for label, _ in resume.contacts)
    for entries in (resume.experience, resume.projects, resume.education):
        for entry in entries:
            values.extend((entry.left, entry.right, entry.subtitle, entry.location))
            values.extend(entry.bullets)
    for label, value in resume.skills:
        values.extend((label, value))
    text = " ".join(filter(None, values))
    return len(re.findall(r"\b[\w+#.-]+\b", text)), len(re.sub(r"\s", "", text))


def _normalize_extended_properties(path: Path, resume: Resume) -> None:
    words, characters = _resume_statistics(resume)
    replacement = path.with_name(f"{path.stem}__metadata.docx")
    ElementTree.register_namespace("", APP_PROPERTIES_NS)
    ElementTree.register_namespace("vt", VT_PROPERTIES_NS)

    with ZipFile(path) as source, ZipFile(replacement, "w") as target:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == "docProps/app.xml":
                root = ElementTree.fromstring(data)
                values = {
                    "Application": "automatic-resume compile_cv.py",
                    "Pages": "1",
                    "Words": str(words),
                    "Characters": str(characters),
                }
                for name, value in values.items():
                    element = root.find(f"{{{APP_PROPERTIES_NS}}}{name}")
                    if element is None:
                        element = ElementTree.SubElement(
                            root,
                            f"{{{APP_PROPERTIES_NS}}}{name}",
                        )
                    element.text = value
                data = ElementTree.tostring(
                    root,
                    encoding="utf-8",
                    xml_declaration=True,
                )
            target.writestr(info, data)
    replacement.replace(path)


def compile_docx(tex_path: Path) -> Path:
    resume = parse_resume(tex_path)
    output = tex_path.with_suffix(".docx")
    temporary = output.with_name(f"{output.stem}__build.docx")
    build_document(resume).save(temporary)
    _normalize_extended_properties(temporary, resume)
    try:
        temporary.replace(output)
        return output
    except OSError:
        fallback = output.with_name(f"{output.stem}_latest.docx")
        temporary.replace(fallback)
        return fallback
