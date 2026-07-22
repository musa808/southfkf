"""
PDF generation helpers for FCMS reports.
Uses ReportLab Platypus (pure Python, works on Windows without system deps).

All functions return a BytesIO object ready to be served as an HttpResponse.
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand colours matching base.html ──────────────────────────────────────────
PITCH_GREEN = colors.HexColor("#1B4332")
GOLD = colors.HexColor("#C9A24B")
CHALK = colors.HexColor("#F7F4ED")
LIGHT_GREY = colors.HexColor("#ECECEC")

# ── Shared styles ──────────────────────────────────────────────────────────────
_base = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "FCMSTitle",
    parent=_base["Title"],
    textColor=PITCH_GREEN,
    fontSize=16,
    spaceAfter=4,
)
SUBTITLE_STYLE = ParagraphStyle(
    "FCMSSubtitle",
    parent=_base["Normal"],
    textColor=colors.HexColor("#555555"),
    fontSize=9,
    spaceAfter=12,
)
BODY_STYLE = ParagraphStyle("FCMSBody", parent=_base["Normal"], fontSize=9)

HEADER_TABLE_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), PITCH_GREEN),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CHALK, colors.white]),
    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
])


def _doc(buffer, title):
    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=title,
    )


def _header(competition, subtitle):
    return [
        Paragraph(f"⚽ {competition.name}", TITLE_STYLE),
        Paragraph(
            f"{competition.season.name}  ·  {subtitle}  ·  Generated {date.today().strftime('%d %b %Y')}",
            SUBTITLE_STYLE,
        ),
        Spacer(1, 0.3 * cm),
    ]


# ── 1. Fixture List ────────────────────────────────────────────────────────────

def generate_fixture_list_pdf(competition):
    """Returns BytesIO of a PDF listing all fixtures for a competition."""
    buffer = io.BytesIO()
    doc = _doc(buffer, f"Fixtures — {competition.name}")

    from fixtures.models import Fixture
    fixtures = (
        Fixture.objects.filter(competition=competition)
        .select_related("home_team__club", "away_team__club", "group", "knockout_fixture__round")
        .order_by("match_date", "kickoff_time")
    )

    story = _header(competition, "Fixture List")

    data = [["#", "Date", "Kickoff", "Home", "Away", "Venue", "Stage"]]
    for i, fx in enumerate(fixtures, 1):
        if fx.is_knockout:
            stage = fx.knockout_fixture.round.get_name_display()
        elif fx.is_group_stage:
            stage = f"{fx.group.name} · MD{fx.round_number}"
        else:
            stage = f"Matchday {fx.round_number}"
            if fx.leg == 2:
                stage += " (R)"

        data.append([
            str(i),
            fx.match_date.strftime("%d %b %Y") if fx.match_date else "TBD",
            fx.kickoff_time.strftime("%H:%M") if fx.kickoff_time else "—",
            fx.home_team.club.name,
            fx.away_team.club.name,
            fx.venue or "—",
            stage,
        ])

    col_widths = [0.6*cm, 2.2*cm, 1.4*cm, 4*cm, 4*cm, 3*cm, 3*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(HEADER_TABLE_STYLE)
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ── 2. Standings Table ─────────────────────────────────────────────────────────

def generate_standings_pdf(competition):
    """Returns BytesIO of a PDF standings table (or per-group tables for group stage)."""
    buffer = io.BytesIO()
    doc = _doc(buffer, f"Standings — {competition.name}")

    from standings.models import StandingsRow
    story = _header(competition, "Standings")

    def _standings_table(rows, title=None):
        if title:
            story.append(Paragraph(title, ParagraphStyle(
                "GroupHead", parent=_base["Heading3"],
                textColor=PITCH_GREEN, spaceAfter=4, spaceBefore=8,
            )))
        data = [["#", "Club", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]]
        for pos, row in enumerate(rows, 1):
            gd = row.goals_for - row.goals_against
            data.append([
                str(pos),
                row.team.club.name,
                str(row.played),
                str(row.won),
                str(row.drawn),
                str(row.lost),
                str(row.goals_for),
                str(row.goals_against),
                f"+{gd}" if gd > 0 else str(gd),
                str(row.points),
            ])
        col_widths = [0.6*cm, 6*cm, 1*cm, 1*cm, 1*cm, 1*cm, 1*cm, 1*cm, 1*cm, 1.2*cm]
        t = Table(data, colWidths=col_widths, repeatRows=1)

        style = TableStyle(list(HEADER_TABLE_STYLE._cmds))
        # Bold the points column
        style.add("FONTNAME", (9, 1), (9, -1), "Helvetica-Bold")
        # Highlight qualifying spots gold (top N teams per group for GROUP_KNOCKOUT)
        if competition.has_groups and title:
            n = competition.teams_qualifying_per_group
            for r in range(1, min(n + 1, len(data))):
                style.add("BACKGROUND", (0, r), (-1, r), colors.HexColor("#E6F4EA"))
        t.setStyle(style)
        story.append(t)

    if competition.has_groups:
        groups = competition.groups.prefetch_related("standings__team__club").order_by("name")
        for group in groups:
            rows = sorted(
                group.standings.all(),
                key=lambda r: (-r.points, -(r.goals_for - r.goals_against), -r.goals_for),
            )
            _standings_table(rows, title=group.name)
    else:
        rows = StandingsRow.objects.filter(competition=competition).select_related("team__club")
        rows = sorted(rows, key=lambda r: (-r.points, -(r.goals_for - r.goals_against), -r.goals_for))
        _standings_table(rows)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ── 3. Top Scorers ─────────────────────────────────────────────────────────────

def generate_top_scorers_pdf(competition):
    """Returns BytesIO of a PDF top-scorers sheet for a competition."""
    buffer = io.BytesIO()
    doc = _doc(buffer, f"Top Scorers — {competition.name}")

    from django.db.models import Count
    from results.models import GoalEvent

    goals_qs = (
        GoalEvent.objects.filter(
            result__fixture__competition=competition,
            is_own_goal=False,
        )
        .values("scorer__id", "scorer__first_name", "scorer__last_name", "scorer__club__name")
        .annotate(goals=Count("id"))
        .order_by("-goals")
    )

    story = _header(competition, "Top Scorers")

    data = [["#", "Player", "Club", "Goals"]]
    for i, row in enumerate(goals_qs, 1):
        if row["scorer__id"] is None:
            continue
        name = f"{row['scorer__first_name']} {row['scorer__last_name']}"
        data.append([str(i), name, row["scorer__club__name"], str(row["goals"])])

    if len(data) == 1:
        story.append(Paragraph("No goals recorded yet.", BODY_STYLE))
    else:
        col_widths = [0.8*cm, 6*cm, 6*cm, 2*cm]
        t = Table(data, colWidths=col_widths, repeatRows=1)
        style = TableStyle(list(HEADER_TABLE_STYLE._cmds))
        style.add("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold")
        style.add("ALIGN", (3, 0), (3, -1), "CENTER")
        t.setStyle(style)
        story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ── 4. Competition Summary ─────────────────────────────────────────────────────

def generate_competition_summary_pdf(competition):
    """
    One-page summary: competition info, standings (or bracket overview),
    top 5 scorers. Useful for sharing with officials / printing at matches.
    """
    buffer = io.BytesIO()
    doc = _doc(buffer, f"Summary — {competition.name}")
    story = _header(competition, "Competition Summary")

    # --- Competition info block ---
    info_data = [
        ["Type", competition.get_competition_type_display()],
        ["Season", competition.season.name],
        ["Status", competition.get_status_display()],
        ["Teams entered", str(competition.entered_teams.count())],
    ]
    if competition.competition_type == "LEAGUE":
        info_data.append(["Format", "Double round-robin" if competition.double_round_robin else "Single round-robin"])
        info_data.append(["Points (W/D/L)", f"{competition.points_win} / {competition.points_draw} / {competition.points_loss}"])

    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), PITCH_GREEN),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CHALK, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    # --- Top 5 scorers mini-table ---
    from django.db.models import Count
    from results.models import GoalEvent
    from standings.models import StandingsRow

    top5 = (
        GoalEvent.objects.filter(result__fixture__competition=competition, is_own_goal=False, scorer__isnull=False)
        .values("scorer__first_name", "scorer__last_name", "scorer__club__name")
        .annotate(g=Count("id"))
        .order_by("-g")[:5]
    )
    if top5:
        story.append(Paragraph("Top Scorers", ParagraphStyle(
            "SectionHead", parent=_base["Heading3"], textColor=PITCH_GREEN, spaceAfter=4,
        )))
        sc_data = [["Player", "Club", "Goals"]] + [
            [f"{r['scorer__first_name']} {r['scorer__last_name']}", r["scorer__club__name"], str(r["g"])]
            for r in top5
        ]
        sc_table = Table(sc_data, colWidths=[5*cm, 7*cm, 2*cm], repeatRows=1)
        sc_table.setStyle(HEADER_TABLE_STYLE)
        story.append(sc_table)
        story.append(Spacer(1, 0.5*cm))

    # --- Standings snippet (league only, top 5) ---
    if not competition.has_groups and competition.affects_standings:
        rows = list(
            StandingsRow.objects.filter(competition=competition)
            .select_related("team__club")
            .order_by("-points", "-goals_for")[:5]
        )
        if rows:
            story.append(Paragraph("Standings (Top 5)", ParagraphStyle(
                "SectionHead", parent=_base["Heading3"], textColor=PITCH_GREEN, spaceAfter=4,
            )))
            st_data = [["#", "Club", "P", "W", "D", "L", "GD", "Pts"]]
            for pos, row in enumerate(rows, 1):
                gd = row.goals_for - row.goals_against
                st_data.append([
                    str(pos), row.team.club.name, str(row.played),
                    str(row.won), str(row.drawn), str(row.lost),
                    f"+{gd}" if gd > 0 else str(gd), str(row.points),
                ])
            col_widths = [0.6*cm, 7*cm, 1*cm, 1*cm, 1*cm, 1*cm, 1.2*cm, 1.2*cm]
            st_table = Table(st_data, colWidths=col_widths, repeatRows=1)
            st_table.setStyle(HEADER_TABLE_STYLE)
            story.append(st_table)

    doc.build(story)
    buffer.seek(0)
    return buffer