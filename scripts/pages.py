# -- coding: utf-8 --
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

width, height = A4

# Colors
beige = HexColor("#f8f4ed")        # background
blue = HexColor("#91a8d0")         # accent
grid = HexColor("#e8e8e8")         # background grid lines (very subtle, lighter)
underline = HexColor("#b0b0b0")    # form field underlines (darker grey)
black = HexColor("#000000")

MARGIN = 40  # general margin
GRID_STEP = 18  # grid spacing (must match set_background step)
TEXT_PADDING = 3  # padding between text baseline and grid line (in points)


def snap_to_grid(y):
    """Snap y position to the nearest grid line."""
    offset = y - MARGIN
    snapped = round(offset / GRID_STEP) * GRID_STEP
    return MARGIN + snapped


def text_above_grid(y):
    """Position text above a grid line with padding."""
    grid_y = snap_to_grid(y)
    return grid_y + TEXT_PADDING


def snap_x_to_grid(x):
    """Snap x position to the nearest vertical grid line."""
    offset = x - MARGIN
    snapped = round(offset / GRID_STEP) * GRID_STEP
    return MARGIN + snapped


def set_background(c, with_grid=True):
    # beige background
    c.setFillColor(beige)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    if with_grid:
        # subtle grid inside margins
        c.setStrokeColor(grid)
        c.setLineWidth(0.25)
        y = MARGIN
        while y <= height - MARGIN:
            c.line(MARGIN, y, width - MARGIN, y)
            y += GRID_STEP
        x = MARGIN
        while x <= width - MARGIN:
            c.line(x, MARGIN, x, height - MARGIN)
            x += GRID_STEP

    c.setFillColor(black)


def header_title(c, text):
    c.setFillColor(black)
    c.setFont("Times-Bold", 22)
    c.drawCentredString(width / 2, height - MARGIN + 5, text)
    # accent line
    c.setStrokeColor(blue)
    c.setLineWidth(2)
    c.line(MARGIN, height - MARGIN - 5, width - MARGIN, height - MARGIN - 5)
    c.setFillColor(black)


# 1. Page d’introduction
def make_page_introduction():
    c = canvas.Canvas("Page_d_introduction.pdf", pagesize=A4)
    set_background(c, with_grid=False)
    header_title(c, u"Mes objectifs en français")

    c.setFont("Times-Roman", 14)

    y = height - MARGIN - 40
    sections = [
        (u"Pourquoi j'apprends le français", 8),
        (u"Mes objectifs à court terme (1–3 mois)", 8),
        (u"Mes objectifs à long terme (6–12 mois)", 8),
        (u"Mes ressources principales", 8),
    ]

    for title, lines in sections:
        c.setFont("Times-Bold", 14)
        # Position header - use minimal padding to be closer to line below
        # Draw text at y position with just a small padding (not full TEXT_PADDING)
        text_y = y + 2  # Small padding above grid line
        c.drawString(MARGIN, text_y, title)
        # Move down less - about half a grid step to get closer to first line
        y = y - (GRID_STEP / 2)  # Half grid step
        y = snap_to_grid(y)  # Snap to grid for alignment
        c.setStrokeColor(underline)
        c.setLineWidth(0.5)
        for _ in range(lines):
            y = snap_to_grid(y - GRID_STEP)
            c.line(MARGIN, y, width - MARGIN, y)
        y = snap_to_grid(y - GRID_STEP)  # Space after section
        c.setFont("Times-Roman", 14)

    c.showPage()
    c.save()


# 2. Journal quotidien
def make_journal_quotidien():
    c = canvas.Canvas("Journal_quotidien.pdf", pagesize=A4)
    set_background(c, with_grid=True)
    header_title(c, u"Journal quotidien")

    c.setFont("Times-Roman", 12)
    y = height - MARGIN - 35

    # Date & objective
    c.setFont("Times-Bold", 12)
    text_y = text_above_grid(y)
    line_y = snap_to_grid(y)
    c.drawString(MARGIN, text_y, u"Date :")
    c.setFont("Times-Roman", 12)
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    c.line(MARGIN + 40, line_y, width / 2, line_y)

    c.setFont("Times-Bold", 12)
    # Ensure text doesn't overflow - check if there's enough space
    obj_text = u"Objectif du jour :"
    obj_width = c.stringWidth(obj_text, "Times-Bold", 12)
    if width / 2 + 10 + obj_width < width - MARGIN:
        c.drawString(width / 2 + 10, text_y, obj_text)
    c.setFont("Times-Roman", 12)
    c.line(width / 2 + 140, line_y, width - MARGIN, line_y)

    y = snap_to_grid(y - GRID_STEP * 2)  # Move down 2 grid lines

    # Vocabulaire du jour
    c.setFont("Times-Bold", 12)
    text_y = text_above_grid(y)
    c.drawString(MARGIN, text_y, u"Vocabulaire du jour :")
    y = snap_to_grid(y - 10)
    c.setStrokeColor(blue)
    c.setLineWidth(1)
    c.line(MARGIN, y, width - MARGIN, y)
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    y = snap_to_grid(y - 8)

    # allocate block
    block_height = 120
    while y > height - MARGIN - 35 - block_height and y > MARGIN + 320:
        c.line(MARGIN, y, width - MARGIN, y)
        y = snap_to_grid(y - GRID_STEP)

    y = snap_to_grid(y - 12)

    # Grammaire / Notes
    c.setFont("Times-Bold", 12)
    text_y = text_above_grid(y)
    c.drawString(MARGIN, text_y, u"Grammaire / Notes :")
    y = snap_to_grid(y - 10)
    c.setStrokeColor(blue)
    c.setLineWidth(1)
    c.line(MARGIN, y, width - MARGIN, y)
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    y = snap_to_grid(y - 8)

    while y > MARGIN + 190:
        c.line(MARGIN, y, width - MARGIN, y)
        y = snap_to_grid(y - GRID_STEP)

    y = snap_to_grid(y - 12)

    # Écoute / Vidéos
    c.setFont("Times-Bold", 12)
    text_y = text_above_grid(y)
    # Ensure text doesn't overflow
    ecoute_text = u"Écoute / Vidéos : (titre, chaîne, notes)"
    ecoute_width = c.stringWidth(ecoute_text, "Times-Bold", 12)
    if MARGIN + ecoute_width < width - MARGIN:
        c.drawString(MARGIN, text_y, ecoute_text)
    else:
        # Truncate if too long
        c.drawString(MARGIN, text_y, u"Écoute / Vidéos :")
    y = snap_to_grid(y - 10)
    c.setStrokeColor(blue)
    c.setLineWidth(1)
    c.line(MARGIN, y, width - MARGIN, y)
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    y = snap_to_grid(y - 8)

    while y > MARGIN + 90:
        c.line(MARGIN, y, width - MARGIN, y)
        y = snap_to_grid(y - GRID_STEP)

    y = snap_to_grid(y - 12)

    # Réflexions / Révision
    c.setFont("Times-Bold", 12)
    text_y = text_above_grid(y)
    c.drawString(MARGIN, text_y, u"Réflexions / Révision :")
    y = snap_to_grid(y - 10)
    c.setStrokeColor(blue)
    c.setLineWidth(1)
    c.line(MARGIN, y, width - MARGIN, y)
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    y = snap_to_grid(y - 8)

    while y > MARGIN:
        c.line(MARGIN, y, width - MARGIN, y)
        y = snap_to_grid(y - GRID_STEP)

    c.showPage()
    c.save()


# 3. Journal de vocabulaire par thème
def make_journal_vocabulaire():
    c = canvas.Canvas("Journal_vocabulaire_par_theme.pdf", pagesize=A4)
    set_background(c, with_grid=True)
    header_title(c, u"Vocabulaire par thème")

    c.setFont("Times-Bold", 12)
    y = height - MARGIN - 35
    text_y = text_above_grid(y)
    line_y = snap_to_grid(y)
    c.drawString(MARGIN, text_y, u"Thème :")
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    c.line(MARGIN + 50, line_y, width - MARGIN, line_y)
    y = snap_to_grid(y - 25)

    # table headers
    c.setFont("Times-Bold", 11)
    col1 = MARGIN
    col2 = col1 + 140
    col3 = col2 + 160
    col4 = col3 + 120

    text_y = text_above_grid(y)
    # Ensure headers don't overflow their columns
    c.drawString(col1, text_y, u"Mot / expression")
    c.drawString(col2, text_y, u"Traduction (IT/EN)")
    c.drawString(col3, text_y, u"Exemple")
    # Check if Notes fits
    notes_width = c.stringWidth(u"Notes", "Times-Bold", 11)
    if col4 + notes_width < width - MARGIN:
        c.drawString(col4, text_y, u"Notes")

    y = snap_to_grid(y - 6)
    c.setStrokeColor(blue)
    c.setLineWidth(1)
    c.line(MARGIN, y, width - MARGIN, y)
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    y = snap_to_grid(y - 10)

    # Draw vertical lines between columns (starting just below header separator)
    header_sep_y = snap_to_grid(y + 10)  # Where the blue separator is
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    for x in [col2, col3, col4]:
        c.line(x, header_sep_y, x, MARGIN)

    # rows
    while y > MARGIN:
        c.line(MARGIN, y, width - MARGIN, y)
        y = snap_to_grid(y - GRID_STEP)

    c.showPage()
    c.save()


# 4. Journal d'écoute
def make_journal_ecoute():
    c = canvas.Canvas("Journal_d_ecoute.pdf", pagesize=A4)
    set_background(c, with_grid=True)
    header_title(c, u"Journal d'écoute")

    c.setFont("Times-Bold", 11)
    # Start closer to header - remove extra space at top
    y = height - MARGIN - 30

    # Use 3 entries with optimized spacing
    for entry_num in range(3):
        # Check if we have enough space before drawing entry
        if y < MARGIN + 180:
            break

        # For second and subsequent entries, start one square above (reduce spacing)
        if entry_num > 0:
            y = snap_to_grid(y - GRID_STEP)  # One square less spacing

        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        c.drawString(MARGIN, text_y, u"Titre / Source :")
        c.setStrokeColor(underline)
        c.setLineWidth(0.5)
        c.line(MARGIN + 80, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)

        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        type_text = u"Type (YouTube, podcast, etc.) :"
        type_width = c.stringWidth(type_text, "Times-Bold", 11)
        if MARGIN + type_width < width - MARGIN:
            c.drawString(MARGIN, text_y, type_text)
        else:
            c.drawString(MARGIN, text_y, u"Type :")
        c.line(MARGIN + 170, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)

        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        c.drawString(MARGIN, text_y, u"Durée :")
        c.line(MARGIN + 45, line_y, MARGIN + 150, line_y)

        date_width = c.stringWidth(u"Date :", "Times-Bold", 11)
        if MARGIN + 170 + date_width < width - MARGIN:
            c.drawString(MARGIN + 170, text_y, u"Date :")
        c.line(MARGIN + 210, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)

        # Sujets / Thèmes - line starts right after the text
        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        sujets_text = u"Sujets / Thèmes :"
        sujets_width = c.stringWidth(sujets_text, "Times-Bold", 11)
        c.drawString(MARGIN, text_y, sujets_text)
        c.setStrokeColor(underline)
        c.setLineWidth(0.5)
        c.line(MARGIN + sujets_width + 5, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)
        # Then writing lines
        for _ in range(2):
            if y <= MARGIN:
                break
            c.line(MARGIN, y, width - MARGIN, y)
            y = snap_to_grid(y - GRID_STEP)

        # Mots / expressions intéressants - first line starts right after the text
        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        mots_text = u"Mots / expressions intéressants :"
        mots_width = c.stringWidth(mots_text, "Times-Bold", 11)
        if MARGIN + mots_width < width - MARGIN:
            c.drawString(MARGIN, text_y, mots_text)
        else:
            mots_text = u"Mots / expressions :"
            mots_width = c.stringWidth(mots_text, "Times-Bold", 11)
            c.drawString(MARGIN, text_y, mots_text)
        # First line starts right after text
        c.line(MARGIN + mots_width + 5, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)
        # Then remaining writing lines
        for _ in range(1):  # One more line
            if y <= MARGIN:
                break
            c.line(MARGIN, y, width - MARGIN, y)
            y = snap_to_grid(y - GRID_STEP)

        # Résumé / Compréhension - first line starts right after the text
        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        resume_text = u"Résumé / Compréhension :"
        resume_width = c.stringWidth(resume_text, "Times-Bold", 11)
        if MARGIN + resume_width < width - MARGIN:
            c.drawString(MARGIN, text_y, resume_text)
        else:
            resume_text = u"Résumé :"
            resume_width = c.stringWidth(resume_text, "Times-Bold", 11)
            c.drawString(MARGIN, text_y, resume_text)
        # First line starts right after text
        c.line(MARGIN + resume_width + 5, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)
        # Then remaining writing lines
        for _ in range(2):  # Two more lines
            if y <= MARGIN:
                break
            c.line(MARGIN, y, width - MARGIN, y)
            y = snap_to_grid(y - GRID_STEP)

        # Blue separator - one square above (reduce spacing before it)
        y = snap_to_grid(y - GRID_STEP)  # One square before separator
        # Only draw separator if we have space - same format as Journal_de_lecture
        if y > MARGIN + 10:
            c.setStrokeColor(blue)
            c.setLineWidth(1.5)  # Thicker blue separator like Journal_de_lecture
            c.line(MARGIN, y, width - MARGIN, y)
        # Space between entries - one square above next entry
        y = snap_to_grid(y - GRID_STEP)

    c.showPage()
    c.save()


# 5. Journal de lecture
def make_journal_lecture():
    c = canvas.Canvas("Journal_de_lecture.pdf", pagesize=A4)
    set_background(c, with_grid=True)
    header_title(c, u"Journal de lecture")

    c.setFont("Times-Bold", 11)
    y = height - MARGIN - 35

    # Use 3 entries for better spacing
    for entry_num in range(3):
        # Check if we have enough space before drawing entry
        if y < MARGIN + 200:
            break

        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        c.drawString(MARGIN, text_y, u"Titre :")
        c.setStrokeColor(underline)
        c.setLineWidth(0.5)
        c.line(MARGIN + 40, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)

        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        auteur_text = u"Auteur / Source :"
        auteur_width = c.stringWidth(auteur_text, "Times-Bold", 11)
        if MARGIN + auteur_width < width - MARGIN:
            c.drawString(MARGIN, text_y, auteur_text)
        else:
            c.drawString(MARGIN, text_y, u"Auteur :")
        c.line(MARGIN + 95, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)

        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        pages_text = u"Pages / Partie lue :"
        pages_width = c.stringWidth(pages_text, "Times-Bold", 11)
        if MARGIN + pages_width < width - MARGIN:
            c.drawString(MARGIN, text_y, pages_text)
        else:
            c.drawString(MARGIN, text_y, u"Pages :")
        c.line(MARGIN + 115, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)

        # Vocabulaire nouveau - first line starts just after the words
        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        vocab_text = u"Vocabulaire nouveau :"
        vocab_width = c.stringWidth(vocab_text, "Times-Bold", 11)
        if MARGIN + vocab_width < width - MARGIN:
            c.drawString(MARGIN, text_y, vocab_text)
        else:
            vocab_text = u"Vocabulaire :"
            vocab_width = c.stringWidth(vocab_text, "Times-Bold", 11)
            c.drawString(MARGIN, text_y, vocab_text)
        # First line starts right after the text
        c.setStrokeColor(underline)
        c.setLineWidth(0.5)
        c.line(MARGIN + vocab_width + 5, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)
        # Then regular spacing for remaining lines
        for _ in range(1):  # One more line
            if y <= MARGIN:
                break
            c.line(MARGIN, y, width - MARGIN, y)
            y = snap_to_grid(y - GRID_STEP)

        # Résumé / Idées principales - first line starts just after the words
        text_y = text_above_grid(y)
        line_y = snap_to_grid(y)
        resume_text = u"Résumé / Idées principales :"
        resume_width = c.stringWidth(resume_text, "Times-Bold", 11)
        if MARGIN + resume_width < width - MARGIN:
            c.drawString(MARGIN, text_y, resume_text)
        else:
            c.drawString(MARGIN, text_y, u"Résumé :")
            resume_width = c.stringWidth(u"Résumé :", "Times-Bold", 11)
        # First line starts right after the text
        c.line(MARGIN + resume_width + 5, line_y, width - MARGIN, line_y)
        y = snap_to_grid(y - GRID_STEP)
        # Then regular spacing for remaining lines
        for _ in range(2):  # Two more lines
            if y <= MARGIN:
                break
            c.line(MARGIN, y, width - MARGIN, y)
            y = snap_to_grid(y - GRID_STEP)

        text_y = text_above_grid(y)
        diffic_text = u"Difficultés / Points à revoir :"
        diffic_width = c.stringWidth(diffic_text, "Times-Bold", 11)
        if MARGIN + diffic_width < width - MARGIN:
            c.drawString(MARGIN, text_y, diffic_text)
        else:
            c.drawString(MARGIN, text_y, u"Difficultés :")
        # Only 1 grid square before first line (not 2)
        y = snap_to_grid(y - GRID_STEP)
        for _ in range(2):
            if y <= MARGIN:
                break
            c.line(MARGIN, y, width - MARGIN, y)
            y = snap_to_grid(y - GRID_STEP)

        y = snap_to_grid(y - GRID_STEP)  # Space before separator
        # Only draw separator if we have space - make it thicker
        if y > MARGIN + 10:
            c.setStrokeColor(blue)
            c.setLineWidth(1.5)  # Thicker blue separator
            c.line(MARGIN, y, width - MARGIN, y)
        y = snap_to_grid(y - GRID_STEP * 2)  # More space between entries

    c.showPage()
    c.save()


# 6. Suivi des progrès
def make_suivi_progres():
    c = canvas.Canvas("Suivi_des_progres.pdf", pagesize=A4)
    set_background(c, with_grid=True)
    header_title(c, u"Suivi des progrès")

    c.setFont("Times-Bold", 11)
    y = height - MARGIN - 40

    headers = [u"Semaine", u"Ressource principale", u"Nouveau vocabulaire",
               u"Thèmes étudiés", u"Confiance /10"]
    num_cols = len(headers)

    # Define proportional widths based on content needs:
    # Semaine: small (numbers only), Ressource: medium, Nouveau vocabulaire: largest,
    # Thèmes: bigger, Confiance: small (numbers only)
    column_weights = [1, 2, 3, 2, 1]  # Proportional weights
    total_weight = sum(column_weights)

    # Calculate column boundaries proportionally, then snap to grid
    available_width = width - 2 * MARGIN
    num_grid_steps = int((available_width) / GRID_STEP)

    # First, ensure minimum widths based on header text
    c.setFont("Times-Bold", 11)
    min_widths = []
    for h_text in headers:
        text_width = c.stringWidth(h_text, "Times-Bold", 11)
        min_widths.append(text_width + 10)  # Add padding

    # Calculate proportional positions
    xs = [MARGIN]  # Start at left margin
    cumulative_weight = 0

    for i in range(num_cols - 1):
        cumulative_weight += column_weights[i]
        # Calculate proportional position
        proportional_pos = (cumulative_weight / total_weight) * available_width
        # Snap to nearest grid step
        grid_steps = round(proportional_pos / GRID_STEP)
        x_pos = MARGIN + (grid_steps * GRID_STEP)
        xs.append(x_pos)

    xs.append(width - MARGIN)  # End at right margin (ensure it's on grid)

    # Ensure each column is at least as wide as its header (adjust if needed)
    for i in range(num_cols):
        col_width = xs[i + 1] - xs[i]
        if col_width < min_widths[i]:
            # Need to expand this column - adjust the right boundary
            new_right = xs[i] + min_widths[i]
            new_right = snap_x_to_grid(new_right)
            # Only adjust if it doesn't break other columns
            if new_right <= xs[i + 1] or (i == num_cols - 1):
                xs[i + 1] = new_right

    # header row - center align text in each column
    text_y = text_above_grid(y)
    for i, h_text in enumerate(headers):
        col_start = xs[i]
        col_end = xs[i + 1]
        col_center = (col_start + col_end) / 2
        text_width = c.stringWidth(h_text, "Times-Bold", 11)
        # Center the text in the column
        text_x = col_center - (text_width / 2)
        # Ensure text doesn't overflow
        if text_x >= col_start and text_x + text_width <= col_end:
            c.drawString(text_x, text_y, h_text)
        else:
            # If too wide, left-align with padding
            c.drawString(col_start + 2, text_y, h_text)

    y = snap_to_grid(y - 6)
    c.setStrokeColor(blue)
    c.setLineWidth(1)
    c.line(MARGIN, y, width - MARGIN, y)
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    y = snap_to_grid(y - 12)

    # Draw vertical lines between columns (starting from header separator)
    # Snap vertical lines to grid vertical lines
    header_sep_y = snap_to_grid(y + 12)  # Where the blue separator is
    c.setStrokeColor(underline)
    c.setLineWidth(0.5)
    for x in xs[1:-1]:  # Skip first and last (margins)
        # Snap x to grid for vertical alignment
        grid_x = snap_x_to_grid(x)
        c.line(grid_x, header_sep_y, grid_x, MARGIN)

    # rows
    while y > MARGIN:
        c.line(MARGIN, y, width - MARGIN, y)
        y = snap_to_grid(y - GRID_STEP)

    c.showPage()
    c.save()


# 7. Page quadrillée libre
def make_page_quadrillee_libre():
    c = canvas.Canvas("Page_quadrillee_libre.pdf", pagesize=A4)
    set_background(c, with_grid=True)
    header_title(c, u"Page quadrillée libre")
    c.showPage()
    c.save()


if __name__ == "__main__":
    make_page_introduction()
    make_journal_quotidien()
    make_journal_vocabulaire()
    make_journal_ecoute()
    make_journal_lecture()
    make_suivi_progres()
    make_page_quadrillee_libre()
    print(u"✅ Tous les templates ont été créés.")
