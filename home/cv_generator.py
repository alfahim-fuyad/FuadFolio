"""Generates an ATS-friendly, modern-styled PDF CV on the fly.

Nothing here is cached longer than the request: GitHub repos are pulled
through `github_api` (which caches for 30 minutes on its own), and Education
+ Profile rows are read straight from the database. That means every click
of "Download CV" reflects whatever is live on GitHub and in /admin/ right
now, with no separate "regenerate" step required.
"""
import io

from django.conf import settings

from about.models import Education
from .github_api import get_github_repos

ACCENT = "#2554e6"
INK = "#0f172a"
DIM = "#475569"
RULE = "#cbd5e1"

MAX_REPOS = 6


def _skills_sections(raw):
    """Parse 'Category: a, b, c' lines into [(category, [skills])]."""
    sections = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            label, rest = line.split(":", 1)
            items = [s.strip() for s in rest.split(",") if s.strip()]
            sections.append((label.strip(), items))
        else:
            sections.append((line, []))
    return sections


def _lines(raw):
    return [l.strip() for l in (raw or "").splitlines() if l.strip()]


def _top_repos():
    repos = get_github_repos() or []
    # Prefer starred/described repos, then most recently pushed.
    ranked = sorted(
        repos,
        key=lambda r: (r.get("stars", 0), r.get("updated_at") or ""),
        reverse=True,
    )
    return ranked[:MAX_REPOS]


def build_cv_pdf(profile):
    """Returns (BytesIO, filename) for the generated PDF."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem,
    )
    from reportlab.lib.styles import ParagraphStyle

    full_name = (profile.full_name if profile else "") or "Md. Al Fahim Fuyad"
    title = (profile.title if profile else "") or "Data Scientist | ML Engineer | AI Builder"
    location = (profile.location if profile else "") or "Dhaka, Bangladesh"
    summary = (profile.summary if profile else "") or ""
    skills = _skills_sections(profile.skills if profile else "")
    experience = _lines(profile.experience if profile else "")
    certifications = _lines(profile.certifications if profile else "")

    username = settings.SITE_GITHUB_USERNAME
    github_url = f"https://github.com/{username}"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        topMargin=20 * mm, bottomMargin=16 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"{full_name} — CV",
    )

    styles = {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=22,
                                textColor=colors.HexColor(INK), leading=26, alignment=TA_LEFT),
        "title": ParagraphStyle("title", fontName="Helvetica", fontSize=12.5,
                                 textColor=colors.HexColor(ACCENT), leading=16, spaceAfter=2),
        "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=9.3,
                                   textColor=colors.HexColor(DIM), leading=13),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5,
                              textColor=colors.HexColor(INK), leading=14,
                              spaceBefore=14, spaceAfter=6, letterSpacing=0.6),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.8,
                                textColor=colors.HexColor(INK), leading=14.5),
        "item_title": ParagraphStyle("item_title", fontName="Helvetica-Bold", fontSize=10.2,
                                      textColor=colors.HexColor(INK), leading=14),
        "item_meta": ParagraphStyle("item_meta", fontName="Helvetica-Oblique", fontSize=9,
                                     textColor=colors.HexColor(DIM), leading=13),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.6,
                                  textColor=colors.HexColor(INK), leading=13.5, leftIndent=2),
        "skill_cat": ParagraphStyle("skill_cat", fontName="Helvetica-Bold", fontSize=9.6,
                                     textColor=colors.HexColor(INK), leading=13.5),
    }

    def rule():
        return HRFlowable(width="100%", thickness=0.8, color=colors.HexColor(RULE),
                           spaceBefore=2, spaceAfter=10)

    def section_heading(text):
        return Paragraph(f'<font color="{ACCENT}">§</font>&nbsp;&nbsp;{text.upper()}', styles["h2"])

    story = []

    story.append(Paragraph(full_name, styles["name"]))
    story.append(Paragraph(title, styles["title"]))
    contact_line = " &nbsp;|&nbsp; ".join([
        location,
        settings.SITE_EMAIL,
        github_url.replace("https://", ""),
        settings.SITE_LINKEDIN_URL.replace("https://", ""),
    ])
    story.append(Paragraph(contact_line, styles["contact"]))
    story.append(Spacer(1, 10))
    story.append(rule())

    if summary:
        story.append(section_heading("Summary"))
        story.append(Paragraph(summary, styles["body"]))

    if skills:
        story.append(section_heading("Skills"))
        for cat, items in skills:
            label = f'<b>{cat}:</b> ' if items else f'<b>{cat}</b>'
            text = label + ", ".join(items) if items else label
            story.append(Paragraph(text, styles["body"]))
            story.append(Spacer(1, 2))

    repos = _top_repos()
    if repos:
        story.append(section_heading("Projects (live from GitHub)"))
        for repo in repos:
            name = repo.get("name") or ""
            desc = repo.get("description") or "No description provided."
            lang = repo.get("language")
            stars = repo.get("stars", 0)
            meta_bits = [b for b in [lang, f"{stars}\u2605" if stars else None] if b]
            meta = " &nbsp;|&nbsp; ".join(meta_bits) if meta_bits else ""
            story.append(Paragraph(f'{name}', styles["item_title"]))
            if meta:
                story.append(Paragraph(meta, styles["item_meta"]))
            story.append(Paragraph(desc, styles["bullet"]))
            story.append(Paragraph(repo.get("url") or "", styles["item_meta"]))
            story.append(Spacer(1, 7))

    if experience:
        story.append(section_heading("Experience"))
        for line in experience:
            if "—" in line or " - " in line:
                sep = "—" if "—" in line else " - "
                head, _, rest = line.partition(sep)
                story.append(Paragraph(head.strip(), styles["item_title"]))
                if rest.strip():
                    story.append(Paragraph(rest.strip(), styles["bullet"]))
            else:
                story.append(Paragraph(line, styles["bullet"]))
            story.append(Spacer(1, 5))

    edu_qs = Education.objects.all()
    if edu_qs.exists():
        story.append(section_heading("Education"))
        for edu in edu_qs:
            head = f"{edu.get_level_display()} — {edu.institution}"
            story.append(Paragraph(head, styles["item_title"]))
            meta_bits = [b for b in [edu.degree, edu.period, edu.location] if b]
            if meta_bits:
                story.append(Paragraph(" &nbsp;|&nbsp; ".join(meta_bits), styles["item_meta"]))
            story.append(Spacer(1, 6))

    if certifications:
        story.append(section_heading("Certifications"))
        story.append(
            ListFlowable(
                [ListItem(Paragraph(c, styles["bullet"]), leftIndent=10) for c in certifications],
                bulletType="bullet", start="circle", leftIndent=8,
            )
        )

    doc.build(story)
    buf.seek(0)

    safe_name = full_name.replace(".", "").replace(" ", "-")
    filename = f"{safe_name}-CV.pdf"
    return buf, filename
