"""Generates an ATS-friendly, visually-designed PDF CV on the fly.

Layout is a two-column "modern resume" (dark photo sidebar + white main
column), matching the reference design the user supplied. Nothing is cached
to disk: GitHub repos come through `github_api` (cached ~30 min on its own),
Education + Profile rows are read straight from the database, and the QR
code links back to this very endpoint — so every click of "Download CV"
reflects whatever is live on GitHub and in /admin/ right now.
"""
import io

from django.conf import settings

from about.models import Education
from .github_api import get_github_repos

# --- palette (kept close to the site's own accent blue) ---------------
ACCENT = colors_hex = "#2554e6"
INK = "#0f172a"
DIM = "#64748b"
SIDEBAR_BG = "#15181f"
SIDEBAR_TEXT = "#e7eaf0"
SIDEBAR_DIM = "#98a2b3"
SIDEBAR_LINE = "#2b2f3a"
PILL_BORDER = "#d7dce6"
RULE = "#d7dce6"

MAX_REPOS = 4
LANG_LEVELS = {
    "native": 1.0, "fluent": 0.95, "professional": 0.85,
    "intermediate": 0.6, "conversational": 0.55, "basic": 0.35,
}

PAGE_W, PAGE_H = None, None  # set inside build_cv_pdf (needs reportlab import)
SIDEBAR_W = 190


def _lines(raw):
    return [l.strip() for l in (raw or "").splitlines() if l.strip()]


def _skills_sections(raw):
    """Parse 'Category: a, b, c' lines into [(category, [skills])]."""
    sections = []
    for line in _lines(raw):
        if ":" in line:
            label, rest = line.split(":", 1)
            items = [s.strip() for s in rest.split(",") if s.strip()]
            sections.append((label.strip(), items))
        else:
            sections.append((line, []))
    return sections


def _interest_tags(raw):
    tags = []
    for line in _lines(raw):
        tags.extend([t.strip() for t in line.split(",") if t.strip()])
    return tags


def _experience_blocks(raw):
    """Blocks separated by a blank line. First line 'Role | Org | Dates', rest are bullets."""
    blocks, current = [], []
    for line in (raw or "").splitlines():
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line.strip())
    if current:
        blocks.append(current)

    entries = []
    for block in blocks:
        head, *bullets = block
        parts = [p.strip() for p in head.split("|")]
        role = parts[0] if len(parts) > 0 else head
        org = parts[1] if len(parts) > 1 else ""
        dates = parts[2] if len(parts) > 2 else ""
        entries.append({"role": role, "org": org, "dates": dates, "bullets": bullets})
    return entries


def _top_repos():
    repos = get_github_repos() or []
    ranked = sorted(repos, key=lambda r: (r.get("stars", 0), r.get("updated_at") or ""), reverse=True)
    return ranked[:MAX_REPOS]


def _circular_photo(profile):
    """Returns a file-like PNG (BytesIO) with a circular, transparent-cornered photo,
    or None if no photo is available (photo section is simply skipped in that case)."""
    from PIL import Image, ImageDraw
    import requests

    raw = None
    try:
        if profile and profile.photo:
            with profile.photo.open('rb') as fh:
                raw = fh.read()
        else:
            from .github_api import get_github_user
            gh = get_github_user()
            if gh and gh.get('avatar_url'):
                resp = requests.get(gh['avatar_url'], timeout=6)
                resp.raise_for_status()
                raw = resp.content
    except Exception:
        raw = None

    if not raw:
        return None

    try:
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        return None

    size = min(img.size)
    left = (img.width - size) // 2
    top = (img.height - size) // 2
    img = img.crop((left, top, left + size, top + size)).resize((300, 300))

    mask = Image.new("L", (300, 300), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 300, 300), fill=255)

    out = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask=mask)

    buf = io.BytesIO()
    out.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _qr_image(url):
    import qrcode
    qr = qrcode.QRCode(border=1, box_size=6)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def build_cv_pdf(profile, cv_url=None):
    """Returns (BytesIO, filename) for the generated PDF.

    `cv_url` (optional absolute URL back to this endpoint) is embedded as a
    QR code in the footer so a printed copy can always be rescanned for the
    latest version.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import (
        BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
        HRFlowable, Table, TableStyle, NextPageTemplate, FrameBreak, KeepTogether,
    )
    from reportlab.platypus.flowables import Flowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfgen import canvas as canvas_mod

    PAGE_W, PAGE_H = A4
    MARGIN = 16 * mm
    SB_W = SIDEBAR_W

    full_name = (profile.full_name if profile else "") or "Md. Al Fahim Fuyad"
    title = (profile.title if profile else "") or "Data Scientist | ML Engineer | AI Builder"
    location = (profile.location if profile else "") or ""
    phone = (profile.phone if profile else "") or ""
    website = (profile.website if profile else "") or ""
    summary = (profile.summary if profile else "") or ""
    skills = _skills_sections(profile.skills if profile else "")
    competencies = _lines(profile.core_competencies if profile else "")
    experience = _experience_blocks(profile.experience if profile else "")
    certifications = _lines(profile.certifications if profile else "")
    achievements = _lines(profile.achievements if profile else "")
    languages = _lines(profile.languages if profile else "")
    interests = _interest_tags(profile.interests if profile else "")
    quote = (profile.quote if profile else "") or ""

    username = settings.SITE_GITHUB_USERNAME
    github_url = f"https://github.com/{username}"
    linkedin_url = settings.SITE_LINKEDIN_URL
    email = settings.SITE_EMAIL

    photo_buf = _circular_photo(profile)

    hw = PAGE_W - SB_W - MARGIN * 2  # header/main column content width
    contact_bits = [b for b in [email, phone, location,
                                 website or github_url.replace("https://", "")] if b]

    # ---------- styles ----------
    styles = {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=21,
                                textColor=colors.HexColor(INK), leading=24),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=9.6,
                                 textColor=colors.HexColor(ACCENT), leading=13, spaceBefore=2,
                                 letterSpacing=1.1),
        "summary": ParagraphStyle("summary", fontName="Helvetica", fontSize=9,
                                   textColor=colors.HexColor(DIM), leading=13.5, spaceBefore=8),
        "contact_row": ParagraphStyle("contact_row", fontName="Helvetica", fontSize=8.3,
                                       textColor=colors.HexColor(DIM), leading=12, spaceBefore=8),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11,
                              textColor=colors.HexColor(INK), leading=13,
                              spaceBefore=13, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9, leading=13.2,
                                textColor=colors.HexColor(INK)),
        "item_title": ParagraphStyle("item_title", fontName="Helvetica-Bold", fontSize=9.6,
                                      textColor=colors.HexColor(INK), leading=13),
        "item_sub": ParagraphStyle("item_sub", fontName="Helvetica-Oblique", fontSize=8.4,
                                    textColor=colors.HexColor(DIM), leading=12),
        "item_date": ParagraphStyle("item_date", fontName="Helvetica-Bold", fontSize=8.2,
                                     textColor=colors.HexColor(ACCENT), leading=12, alignment=2),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=8.7,
                                  textColor=colors.HexColor(INK), leading=12.6, leftIndent=10,
                                  bulletIndent=0, spaceAfter=2),
        "mini_h": ParagraphStyle("mini_h", fontName="Helvetica-Bold", fontSize=9.6,
                                  textColor=colors.HexColor(INK), leading=12, spaceBefore=10, spaceAfter=4),
        "quote": ParagraphStyle("quote", fontName="Helvetica-Oblique", fontSize=8.6,
                                 textColor=colors.HexColor(DIM), leading=12.5, alignment=2),
        "qr_caption": ParagraphStyle("qr_caption", fontName="Helvetica", fontSize=7.6,
                                      textColor=colors.HexColor(DIM), leading=10.5),
        # sidebar (dark bg) styles
        "sb_h": ParagraphStyle("sb_h", fontName="Helvetica-Bold", fontSize=9.3,
                                textColor=colors.HexColor(SIDEBAR_TEXT), leading=12, spaceBefore=14, spaceAfter=5,
                                letterSpacing=0.8),
        "sb_body": ParagraphStyle("sb_body", fontName="Helvetica", fontSize=8.3,
                                   textColor=colors.HexColor(SIDEBAR_DIM), leading=12.2),
        "sb_item": ParagraphStyle("sb_item", fontName="Helvetica", fontSize=8.3,
                                   textColor=colors.HexColor(SIDEBAR_TEXT), leading=12.5),
    }

    # ---------- dynamic header height (name/title/summary/contact can vary in length) ----------
    NAME_TITLE_H = 46
    _summary_p = Paragraph(summary, styles["summary"]) if summary else None
    _sw, _sh = _summary_p.wrap(hw, 1000) if _summary_p else (0, 0)
    _contact_p = Paragraph("   |   ".join(contact_bits), styles["contact_row"]) if contact_bits else None
    _cw, _ch = _contact_p.wrap(hw, 1000) if _contact_p else (0, 0)
    HEADER_H = NAME_TITLE_H + _sh + _ch + 26

    # ---------- small vector helpers ----------
    def pill_row(c, x, y, items, max_w, fill=colors.white, border=PILL_BORDER,
                 text_color=INK, font_size=7.6, pad_x=7, pad_y=4, gap=5, line_gap=6):
        """Draws wrapped rounded-rect tag pills starting at (x,y) [top-left origin],
        returns the y coordinate after the last row."""
        c.setFont("Helvetica", font_size)
        cx, cy = x, y
        row_h = font_size + pad_y * 2
        for item in items:
            w = c.stringWidth(item, "Helvetica", font_size) + pad_x * 2
            if cx + w > x + max_w and cx > x:
                cx = x
                cy -= row_h + line_gap
            c.setFillColor(colors.HexColor(fill) if isinstance(fill, str) else fill)
            c.setStrokeColor(colors.HexColor(border))
            c.roundRect(cx, cy - row_h, w, row_h, row_h / 2, stroke=1, fill=1)
            c.setFillColor(colors.HexColor(text_color))
            c.drawString(cx + pad_x, cy - row_h + pad_y + 1.5, item)
            cx += w + gap
        return cy - row_h

    def lang_bar(c, x, y, width, label, level_word):
        frac = LANG_LEVELS.get((level_word or "").strip().lower(), 0.7)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor(SIDEBAR_TEXT))
        c.drawString(x, y, label)
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor(SIDEBAR_DIM))
        c.drawRightString(x + width, y, level_word.title() if level_word else "")
        bar_y = y - 7
        c.setFillColor(colors.HexColor(SIDEBAR_LINE))
        c.roundRect(x, bar_y, width, 3, 1.5, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(ACCENT))
        c.roundRect(x, bar_y, max(width * frac, 6), 3, 1.5, stroke=0, fill=1)

    def badge(c, cx, cy, r, label, bg=ACCENT, fg=colors.white):
        c.setFillColor(colors.HexColor(bg) if isinstance(bg, str) else bg)
        c.circle(cx, cy, r, stroke=0, fill=1)
        c.setFillColor(fg)
        c.setFont("Helvetica-Bold", r * 0.85)
        c.drawCentredString(cx, cy - r * 0.35, label)

    # ---------- page decoration (sidebar + header), page 1 only ----------
    def draw_page1_decoration(c, doc):
        c.saveState()
        # dark sidebar panel spanning full height
        c.setFillColor(colors.HexColor(SIDEBAR_BG))
        c.rect(0, 0, SB_W, PAGE_H, stroke=0, fill=1)

        pad = 18
        sb_x = pad
        sb_w = SB_W - pad * 2
        y = PAGE_H - 30

        # photo
        if photo_buf is not None:
            photo_r = 42
            photo_cx = SB_W / 2
            photo_cy = y - photo_r
            c.saveState()
            path = c.beginPath()
            path.circle(photo_cx, photo_cy, photo_r)
            c.clipPath(path, stroke=0, fill=0)
            c.drawImage(ImageReader(photo_buf), photo_cx - photo_r, photo_cy - photo_r,
                        width=photo_r * 2, height=photo_r * 2, mask='auto')
            c.restoreState()
            c.setStrokeColor(colors.HexColor(ACCENT))
            c.setLineWidth(2)
            c.circle(photo_cx, photo_cy, photo_r, stroke=1, fill=0)
            y = photo_cy - photo_r - 22
        else:
            y -= 6

        def sb_heading(text):
            nonlocal y
            c.setFillColor(colors.HexColor(ACCENT))
            c.circle(sb_x + 2.5, y - 3, 2.5, stroke=0, fill=1)
            c.setFillColor(colors.HexColor(SIDEBAR_TEXT))
            c.setFont("Helvetica-Bold", 9.2)
            c.drawString(sb_x + 11, y - 6.5, text.upper())
            y -= 16

        def sb_para(text, size=8.1, color=SIDEBAR_DIM, leading=11.6, gap_after=6):
            nonlocal y
            from reportlab.platypus import Paragraph as P
            style = ParagraphStyle("tmp", fontName="Helvetica", fontSize=size,
                                    textColor=colors.HexColor(color), leading=leading)
            p = P(text, style)
            w, h = p.wrap(sb_w, 400)
            p.drawOn(c, sb_x, y - h)
            y -= h + gap_after

        if summary:
            sb_heading("About Me")
            sb_para(summary)

        contact_rows = [b for b in [
            (phone, "Phone"), (email, "Email"), (location, "Location"),
            (github_url.replace("https://", ""), "GitHub"),
            (linkedin_url.replace("https://", "") if linkedin_url else "", "LinkedIn"),
            (website.replace("https://", "") if website else "", "Web"),
        ] if b[0]]
        if contact_rows:
            sb_heading("Contact")
            for value, _label in contact_rows:
                sb_para(value, gap_after=4)
            y -= 4

        if skills:
            sb_heading("Skills")
            for cat, items in skills:
                c.setFont("Helvetica-Bold", 7.8)
                c.setFillColor(colors.HexColor(SIDEBAR_TEXT))
                c.drawString(sb_x, y - 6, cat)
                y -= 14
                if items:
                    y = pill_row(c, sb_x, y, items, sb_w, fill=SIDEBAR_LINE,
                                 border=SIDEBAR_LINE, text_color=SIDEBAR_TEXT, font_size=7.2,
                                 pad_x=6, pad_y=3.2, gap=4, line_gap=4)
                y -= 8

        if competencies:
            sb_heading("Core Competencies")
            for item in competencies:
                c.setFillColor(colors.HexColor(ACCENT))
                c.circle(sb_x + 1.6, y - 5.2, 1.6, stroke=0, fill=1)
                from reportlab.platypus import Paragraph as P
                style = ParagraphStyle("tmp2", fontName="Helvetica", fontSize=8,
                                        textColor=colors.HexColor(SIDEBAR_TEXT), leading=11.4)
                p = P(item, style)
                w, h = p.wrap(sb_w - 9, 200)
                p.drawOn(c, sb_x + 9, y - h)
                y -= h + 4
            y -= 4

        if languages:
            sb_heading("Languages")
            for line in languages:
                if ":" in line:
                    lbl, lvl = line.split(":", 1)
                else:
                    lbl, lvl = line, ""
                lang_bar(c, sb_x, y, sb_w, lbl.strip(), lvl.strip())
                y -= 20

        if interests:
            sb_heading("Interests")
            y = pill_row(c, sb_x, y, interests, sb_w, fill=SIDEBAR_LINE, border=SIDEBAR_LINE,
                         text_color=SIDEBAR_TEXT, font_size=7.2, pad_x=6, pad_y=3.2, gap=4, line_gap=4)

        # ---------- header (right column) ----------
        hx = SB_W + MARGIN
        hy = PAGE_H - MARGIN - 4

        c.setFillColor(colors.HexColor(INK))
        c.setFont("Helvetica-Bold", 21)
        c.drawString(hx, hy - 18, full_name)

        # top-right circular badges: GitHub / LinkedIn / Email
        bx = PAGE_W - MARGIN - 14
        badge(c, bx, hy - 12, 12, "@")
        bx -= 30
        badge(c, bx, hy - 12, 12, "in")
        bx -= 30
        badge(c, bx, hy - 12, 12, "Gh")

        c.setFillColor(colors.HexColor(ACCENT))
        c.setFont("Helvetica-Bold", 9.6)
        c.drawString(hx, hy - 34, title.upper())

        cursor_y = hy - 38
        if _summary_p:
            _summary_p.drawOn(c, hx, cursor_y - _sh)
            cursor_y -= _sh + 10

        if _contact_p:
            _contact_p.drawOn(c, hx, cursor_y - _ch)

        c.setStrokeColor(colors.HexColor(RULE))
        c.setLineWidth(0.8)
        c.line(hx, PAGE_H - HEADER_H, PAGE_W - MARGIN, PAGE_H - HEADER_H)

        c.restoreState()

    def draw_later_decoration(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor(DIM))
        c.setFont("Helvetica", 7.5)
        c.drawRightString(PAGE_W - MARGIN, 12, f"{full_name} — CV (continued)")
        c.restoreState()

    # ---------- frames / doc ----------
    main_frame_1 = Frame(SB_W + MARGIN, MARGIN, PAGE_W - SB_W - MARGIN * 2,
                          PAGE_H - HEADER_H - MARGIN, id="main1",
                          leftPadding=0, rightPadding=0, topPadding=6, bottomPadding=0)
    main_frame_later = Frame(MARGIN, MARGIN, PAGE_W - MARGIN * 2, PAGE_H - MARGIN * 2,
                              id="main_later", leftPadding=0, rightPadding=0, topPadding=6, bottomPadding=0)

    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, title=f"{full_name} — CV")
    doc.addPageTemplates([
        PageTemplate(id="Page1", frames=[main_frame_1], onPage=draw_page1_decoration),
        PageTemplate(id="Later", frames=[main_frame_later], onPage=draw_later_decoration),
    ])

    def rule():
        return HRFlowable(width="100%", thickness=0.7, color=colors.HexColor(RULE),
                           spaceBefore=2, spaceAfter=8)

    def section_heading(text):
        return Paragraph(f'<font color="{ACCENT}">&#8226;</font>&nbsp; {text.upper()}', styles["h2"])

    story = [NextPageTemplate("Later")]

    if experience:
        story.append(section_heading("Experience"))
        for entry in experience:
            head_tbl = Table(
                [[Paragraph(entry["role"], styles["item_title"]),
                  Paragraph(entry["dates"], styles["item_date"])]],
                colWidths=["*", 110],
            )
            head_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            block = [head_tbl]
            if entry["org"]:
                block.append(Paragraph(entry["org"], styles["item_sub"]))
            for b in entry["bullets"]:
                block.append(Paragraph(f"&#8226;&nbsp; {b}", styles["bullet"]))
            block.append(Spacer(1, 8))
            story.append(KeepTogether(block))

    repos = _top_repos()
    if repos:
        story.append(section_heading("Projects"))
        story.append(Paragraph(f'View all projects: {github_url.replace("https://", "")}', styles["item_sub"]))
        story.append(Spacer(1, 4))
        for repo in repos:
            name = repo.get("name") or ""
            desc = repo.get("description") or "No description provided."
            stars = repo.get("stars", 0)
            lang = repo.get("language")
            tag_bits = [t for t in [lang] if t]
            tags_html = "".join(
                f'<font color="white" backColor="{ACCENT}">&nbsp;{t}&nbsp;</font>&nbsp;' for t in tag_bits
            )
            star_html = f' &nbsp;&#9733; {stars}' if stars else ""
            row = Table(
                [[Paragraph(f'<b>{name}</b> {tags_html}', styles["item_title"]),
                  Paragraph(star_html, styles["item_date"])]],
                colWidths=["*", 50],
            )
            row.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            block = [row, Paragraph(desc, styles["body"]), Spacer(1, 8)]
            story.append(KeepTogether(block))

    edu_qs = list(Education.objects.all())
    if edu_qs:
        story.append(section_heading("Education"))
        for edu in edu_qs:
            head_tbl = Table(
                [[Paragraph(f"{edu.get_level_display()} — {edu.institution}", styles["item_title"]),
                  Paragraph(edu.period or "", styles["item_date"])]],
                colWidths=["*", 110],
            )
            head_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            meta_bits = [b for b in [edu.degree, edu.location] if b]
            block = [head_tbl]
            if meta_bits:
                block.append(Paragraph("  |  ".join(meta_bits), styles["item_sub"]))
            block.append(Spacer(1, 8))
            story.append(KeepTogether(block))

    if certifications or achievements:
        story.append(section_heading("Certifications & Achievements"))
        cert_flows = [Paragraph(f"&#8226;&nbsp; {c}", styles["bullet"]) for c in certifications] or \
                     [Paragraph("&mdash;", styles["bullet"])]
        ach_flows = [Paragraph(f"&#8226;&nbsp; {a}", styles["bullet"]) for a in achievements] or \
                    [Paragraph("&mdash;", styles["bullet"])]
        two_col = Table([[cert_flows, ach_flows]], colWidths=["50%", "50%"])
        two_col.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(two_col)
        story.append(Spacer(1, 10))

    # ---------- footer: QR + quote ----------
    class _QRFooter(Flowable):
        def __init__(self, url, quote_text):
            super().__init__()
            self.url = url
            self.quote_text = quote_text
            self.width = 0
            self.height = 62

        def wrap(self, availWidth, availHeight):
            self.width = availWidth
            return self.width, self.height

        def draw(self):
            c = self.canv
            c.setStrokeColor(colors.HexColor(RULE))
            c.setLineWidth(0.7)
            c.line(0, self.height - 2, self.width, self.height - 2)
            if self.url:
                try:
                    qr_buf = _qr_image(self.url)
                    c.drawImage(ImageReader(qr_buf), 0, 4, width=42, height=42)
                    from reportlab.platypus import Paragraph as P
                    cap = P(f'<b>Download My CV</b><br/>Scan the QR code or visit<br/>{self.url}',
                            styles["qr_caption"])
                    w, h = cap.wrap(self.width * 0.5, 42)
                    cap.drawOn(c, 50, 22)
                except Exception:
                    pass
            if self.quote_text:
                from reportlab.platypus import Paragraph as P
                q = P(f'&ldquo;{self.quote_text}&rdquo;', styles["quote"])
                w, h = q.wrap(self.width * 0.45, 42)
                q.drawOn(c, self.width - w, 20)

    story.append(Spacer(1, 4))
    story.append(_QRFooter(cv_url, quote))

    doc.build(story)
    buf.seek(0)

    safe_name = full_name.replace(".", "").replace(" ", "-")
    filename = f"{safe_name}-CV.pdf"
    return buf, filename
