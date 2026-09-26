#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["reportlab>=4"]
# ///
"""Generate synthetic, fictional patient-portal PDFs for tests and evals.

Every person, facility, date, and value here is invented. The layout imitates the structure of
Epic MyChart "Test Details" and clinical-note PDFs closely enough to exercise the extractors.

    python tests/fixtures/generate.py            # rebuild case-a and case-b

Case A is a hospital admission for acute liver injury, seeded with the traps the independent
consult must catch. Case B is a community-acquired pneumonia where the treating team is right,
so the consult must not manufacture doubt. expected.json in each case records the seeded values
and traps that tests assert against.
"""
import json
import os
import shutil
import textwrap

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = letter


class Doc:
    """A minimal page writer: one header per page, lines flow down, pages break automatically."""

    def __init__(self, path, header):
        self.c = canvas.Canvas(path, pagesize=letter)
        self.header = header
        self.y = 0
        self._new_page()

    def _new_page(self):
        if self.y:
            self.c.showPage()
        self.c.setFont("Helvetica", 8)
        self.c.drawString(40, H - 30, self.header)
        self.y = H - 55

    def _need(self, h):
        if self.y - h < 50:
            self._new_page()

    def line(self, text="", x=40, size=10, bold=False):
        self._need(size + 4)
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        self.c.drawString(x, self.y, text)
        self.y -= size + 4

    def para(self, text, size=10, width=95):
        for raw in text.split("\n"):
            for ln in textwrap.wrap(raw, width) or [""]:
                self.line(ln, size=size)

    def row(self, left, right, size=10):
        """Two independent columns on one baseline, as MyChart lays out a two-column panel."""
        self._need(size + 4)
        self.c.setFont("Helvetica", size)
        if left:
            self.c.drawString(40, self.y, left)
        if right:
            self.c.drawString(330, self.y, right)
        self.y -= size + 4

    def save(self):
        self.c.save()


def ticks(lo, hi):
    """Axis tick labels as text extraction renders them, every character doubled."""
    return "   ".join("".join(ch * 2 for ch in str(v)) for v in (lo, hi))


def analyte_block(d, name, value, flag, ref, unit, lo, hi):
    d.line(name, bold=True)
    d.line(f"Normal range: {ref} {unit}".rstrip(), size=9)
    d.line("Value", size=8)
    d.line(f"{value} {flag}".rstrip())
    d.line(ticks(lo, hi), size=7)
    d.line()


def result(folder, fname, patient, title, collected, resulted, analytes=None, two_col=None, body=None,
           deviation=None, empty=False):
    path = os.path.join(folder, fname)
    d = Doc(path, patient["header"])
    d.line(title, size=14, bold=True)
    d.line(f"Collected on {collected}    |    Result date: {resulted}", size=9)
    d.line(f"Ordering provider: {patient['attending']}    Resulting lab: {patient['lab']}", size=8)
    d.line()
    if empty:
        d.line("Results", bold=True)
        d.line("")
    for a in analytes or []:
        analyte_block(d, *a)
    if two_col:
        pairs = [two_col[i:i + 2] for i in range(0, len(two_col), 2)]
        for pair in pairs:
            left, right = pair[0], (pair[1] if len(pair) > 1 else None)
            d.row(left[0], right[0] if right else "")
            d.row(f"Normal range: {left[3]} {left[4]}", f"Normal range: {right[3]} {right[4]}" if right else "", 9)
            d.row(f"{left[1]} {left[2]}".rstrip(), f"{right[1]} {right[2]}".rstrip() if right else "")
            d.row(ticks(left[5], left[6]), ticks(right[5], right[6]) if right else "", 7)
            d.row("", "")
    if body:
        d.para(body)
    if deviation:
        d.line()
        d.line("Lab comment", bold=True)
        d.para(deviation)
    d.line()
    d.line(f"Specimen collected: {collected}", size=8)
    d.save()


def note(folder, fname, patient, note_type, signed, title, sections):
    path = os.path.join(folder, fname)
    d = Doc(path, patient["header"])
    d.line(note_type, size=12, bold=True)
    d.line(f"Signed: {signed}", size=9)
    d.line(title, size=11, bold=True)
    d.line()
    for heading, text in sections:
        d.line(heading, bold=True)
        d.para(text)
        d.line()
    d.save()


# ---------------------------------------------------------------------------------------------
# Case A: acute hepatocellular injury, fictional patient "Alex Fixture"
# ---------------------------------------------------------------------------------------------

A_PATIENT = {
    "header": "Name: Alex Fixture | DOB: 2/14/1963 | MRN: 99900001 | Example General Hospital",
    "attending": "Dana Placeholder, MD",
    "lab": "Example General Core Lab",
}

CMP_REFS = [
    ("Sodium", "136 - 145", "mmol/L", 136, 145),
    ("Potassium", "3.5 - 5.1", "mmol/L", 3.5, 5.1),
    ("Chloride", "98 - 107", "mmol/L", 98, 107),
    ("CO2", "22 - 29", "mmol/L", 22, 29),
    ("BUN", "8 - 23", "mg/dL", 8, 23),
    ("Creatinine", "0.70 - 1.30", "mg/dL", 0.7, 1.3),
    ("Glucose", "70 - 99", "mg/dL", 70, 99),
    ("Calcium, Total", "8.6 - 10.3", "mg/dL", 8.6, 10.3),
    ("Albumin", "3.5 - 5.2", "g/dL", 3.5, 5.2),
    ("Bilirubin, Total", "0.2 - 1.2", "mg/dL", 0.2, 1.2),
    ("Alkaline Phosphatase", "40 - 129", "U/L", 40, 129),
    ("AST", "10 - 40", "U/L", 10, 40),
    ("ALT", "7 - 56", "U/L", 7, 56),
]


def flag(v, lo, hi):
    v = float(v)
    return "High" if v > hi else "Low" if v < lo else ""


def cmp(values):
    out = []
    for (name, ref, unit, lo, hi), v in zip(CMP_REFS, values):
        out.append((name, v, flag(v, lo, hi), ref, unit, lo, hi))
    return out


def build_case_a(root):
    tr = os.path.join(root, "Test Results")
    cn = os.path.join(root, "Care Team Notes")
    os.makedirs(tr)
    os.makedirs(cn)
    P = A_PATIENT
    expected = {"labs": [], "traps": {}}

    cmps = [
        ("Comprehensive Metabolic Panel.pdf", "Mar 3, 2025 6:10 AM", "Mar 3, 2025 7:02 AM",
         ["136", "4.1", "101", "24", "18", "0.92", "104", "9.1", "3.4", "3.8", "162", "842", "1120"]),
        ("Comprehensive Metabolic Panel 2.pdf", "Mar 4, 2025 5:55 AM", "Mar 4, 2025 6:48 AM",
         ["137", "4.0", "102", "23", "17", "0.88", "98", "8.9", "3.2", "4.6", "171", "690", "980"]),
        ("Comprehensive Metabolic Panel 3.pdf", "Mar 5, 2025 6:05 AM", "Mar 5, 2025 7:10 AM",
         ["135", "3.8", "101", "23", "15", "0.85", "92", "8.8", "3.1", "5.9", "180", "512", "845"]),
        ("Comprehensive Metabolic Panel 4.pdf", "Mar 6, 2025 6:00 AM", "Mar 6, 2025 6:59 AM",
         ["134", "3.6", "100", "22", "14", "0.83", "88", "8.7", "2.9", "7.2", "188", "401", "702"]),
    ]
    for fname, coll, res, vals in cmps:
        rows = cmp(vals)
        result(tr, fname, P, "Comprehensive Metabolic Panel", coll, res, analytes=rows)
        expected["labs"] += [{"file": fname, "analyte": r[0], "value": r[1]} for r in rows]

    cbc_refs = [
        ("WBC", "4.0 - 10.5", "K/uL", 4.0, 10.5), ("Hemoglobin", "13.5 - 17.5", "g/dL", 13.5, 17.5),
        ("Hematocrit", "40.0 - 52.0", "%", 40, 52), ("Platelet Count", "150 - 400", "K/uL", 150, 400),
        ("MCV", "80 - 100", "fL", 80, 100), ("RDW-CV", "11.5 - 14.5", "%", 11.5, 14.5),
    ]
    for fname, coll, res, vals in [
        ("Complete Blood Count with Differential.pdf", "Mar 3, 2025 6:10 AM", "Mar 3, 2025 6:40 AM",
         ["7.2", "12.1", "36.0", "142", "91", "14.9"]),
        # Trap: uppercase extension.
        ("Complete Blood Count with Differential 2.PDF", "Mar 5, 2025 6:05 AM", "Mar 5, 2025 6:31 AM",
         ["6.8", "11.6", "34.8", "118", "92", "15.2"]),
    ]:
        rows = [(n, v, flag(v, lo, hi), ref, u, lo, hi) for (n, ref, u, lo, hi), v in zip(cbc_refs, vals)]
        result(tr, fname, P, "Complete Blood Count with Differential", coll, res, two_col=rows)
        expected["labs"] += [{"file": fname, "analyte": r[0], "value": r[1]} for r in rows]
    expected["traps"]["uppercase_extension"] = "Complete Blood Count with Differential 2.PDF"

    for fname, coll, res, pt, inr in [
        ("Prothrombin Time and INR.pdf", "Mar 3, 2025 6:10 AM", "Mar 3, 2025 7:15 AM", "15.8", "1.4"),
        ("Prothrombin Time and INR 2.pdf", "Mar 5, 2025 6:05 AM", "Mar 5, 2025 7:20 AM", "18.9", "1.7"),
    ]:
        rows = [("PT Sec", pt, "High", "11.5 - 14.5", "sec", 11.5, 14.5),
                ("INR", inr, "High", "0.9 - 1.1", "", 0.9, 1.1)]
        result(tr, fname, P, "Prothrombin Time and INR", coll, res, analytes=rows)
        expected["labs"] += [{"file": fname, "analyte": r[0], "value": r[1]} for r in rows]

    singles = [
        ("Acetaminophen Level.pdf", "Acetaminophen Level", "Mar 3, 2025 6:10 AM", "Mar 3, 2025 7:30 AM",
         [("Acetaminophen", "<10", "", "10 - 30", "ug/mL", 10, 30)]),
        ("Lipase.pdf", "Lipase", "Mar 3, 2025 6:10 AM", "Mar 3, 2025 7:02 AM",
         [("Lipase", "38", "", "13 - 60", "U/L", 13, 60)]),
        ("Lactate.pdf", "Lactate, Plasma", "Mar 3, 2025 6:10 AM", "Mar 3, 2025 6:35 AM",
         [("Lactate", "1.4", "", "0.5 - 2.2", "mmol/L", 0.5, 2.2)]),
        ("Ammonia.pdf", "Ammonia", "Mar 5, 2025 3:20 PM", "Mar 5, 2025 4:05 PM",
         [("Ammonia", "68", "High", "16 - 53", "umol/L", 16, 53)]),
        ("Immunoglobulin G.pdf", "Immunoglobulin G", "Mar 4, 2025 9:30 AM", "Mar 5, 2025 11:00 AM",
         [("Immunoglobulin G", "1890", "High", "700 - 1600", "mg/dL", 700, 1600)]),
    ]
    for fname, title, coll, res, rows in singles:
        result(tr, fname, P, title, coll, res, analytes=rows)
        expected["labs"] += [{"file": fname, "analyte": r[0], "value": r[1]} for r in rows]

    result(tr, "Hepatitis Panel, Acute.pdf", P, "Hepatitis Panel, Acute", "Mar 3, 2025 6:10 AM",
           "Mar 3, 2025 2:44 PM", body=(
               "Hepatitis A IgM Antibody: Nonreactive\nHepatitis B Surface Antigen: Nonreactive\n"
               "Hepatitis B Core IgM Antibody: Nonreactive\nHepatitis C Antibody: Nonreactive"))
    # Trap: negative test on a compromised specimen, with the lab's deviation note printed.
    result(tr, "Hepatitis C RNA, Quantitative PCR.pdf", P, "Hepatitis C RNA, Quantitative PCR",
           "Mar 4, 2025 9:30 AM", "Mar 8, 2025 10:12 AM", body="HCV RNA: Not detected",
           deviation=("Specimen received outside the validated stability window (greater than 72 hours from "
                      "collection). Result may be falsely negative. Recollection recommended if clinically "
                      "indicated."))
    expected["traps"]["compromised_specimen"] = "Hepatitis C RNA, Quantitative PCR.pdf"
    result(tr, "Antinuclear Antibody Screen.pdf", P, "Antinuclear Antibody Screen", "Mar 4, 2025 9:30 AM",
           "Mar 5, 2025 1:15 PM", body="ANA Screen, IFA: Negative")
    # Trap: a test whose name contains none of the obvious search terms.
    result(tr, "Miscellaneous Send Out Test.pdf", P, "Miscellaneous Send Out Test", "Mar 4, 2025 9:30 AM",
           "Mar 7, 2025 4:48 PM", analytes=[
               ("F-Actin (Smooth Muscle) Antibody, IgG", "38", "High", "0 - 19", "Units", 0, 19)],
           body="Performed at reference laboratory. Interpretation: Positive (greater than 30 Units: strong positive).")
    expected["labs"].append({"file": "Miscellaneous Send Out Test.pdf",
                             "analyte": "F-Actin (Smooth Muscle) Antibody, IgG", "value": "38"})
    expected["traps"]["oddly_named_test"] = "Miscellaneous Send Out Test.pdf"
    # Trap: a released result page with no result printed.
    result(tr, "Ceruloplasmin.pdf", P, "Ceruloplasmin", "Mar 4, 2025 9:30 AM", "Mar 6, 2025 8:00 AM", empty=True)
    expected["traps"]["empty_result"] = "Ceruloplasmin.pdf"
    result(tr, "Urinalysis with Microscopy.pdf", P, "Urinalysis with Microscopy", "Mar 3, 2025 7:40 AM",
           "Mar 3, 2025 8:20 AM", body=("Color: Dark amber\nBilirubin, Urine: Positive (A)\nUrobilinogen: 4.0 mg/dL (A)\n"
                                        "Protein: Negative\nBlood: Negative\nLeukocyte Esterase: Negative"))

    # Imaging. Trap: the "Collected on" line is the order time. The narrative carries the exam time.
    # Trap: two reads of the hepatic veins disagree, and the confirming addendum was written after the
    # reader knew the CT result, so it is not independent.
    result(tr, "US Abdomen Complete with Doppler.pdf", P, "US Abdomen Complete with Doppler",
           "Mar 3, 2025 8:02 AM", "Mar 3, 2025 3:30 PM", body=(
               "IMPRESSION:\n1. Hepatomegaly (liver 19.2 cm) with coarsened, heterogeneous echotexture.\n"
               "2. Hepatic veins patent with phasic flow.\n3. No biliary ductal dilation. Gallbladder unremarkable.\n"
               "4. Small volume ascites.\n\nNARRATIVE:\nExam performed: 3/3/2025 2:40 PM. Indication: elevated liver "
               "enzymes, jaundice. Grayscale and color Doppler imaging of the abdomen. The portal vein is patent with "
               "hepatopetal flow. The middle and right hepatic veins are visualized and patent. The left hepatic vein "
               "is incompletely visualized due to body habitus.\n\n"
               "ADDENDUM (3/4/2025 4:12 PM): Images re-reviewed at the request of the primary team in light of the CT "
               "performed 3/4/2025. The middle and right hepatic veins are again felt to be patent. The left hepatic "
               "vein remains incompletely visualized."))
    result(tr, "CT Abdomen Pelvis with IV Contrast.pdf", P, "CT Abdomen Pelvis with IV Contrast",
           "Mar 4, 2025 10:15 AM", "Mar 4, 2025 1:05 PM", body=(
               "IMPRESSION:\n1. Hepatomegaly with heterogeneous, mosaic enhancement of the liver parenchyma.\n"
               "2. The hepatic veins are not well opacified on this portal venous phase study. Hepatic venous outflow "
               "obstruction cannot be excluded. Recommend dedicated multiphase liver imaging or Doppler correlation.\n"
               "3. Caudate lobe enlargement.\n4. Small volume ascites.\n\nNARRATIVE:\nExam performed: 3/4/2025 11:02 AM."))
    expected["traps"]["disagreeing_imaging"] = ["US Abdomen Complete with Doppler.pdf",
                                                "CT Abdomen Pelvis with IV Contrast.pdf"]
    expected["traps"]["non_independent_confirmation"] = "US Abdomen Complete with Doppler.pdf (addendum 3/4 4:12 PM)"
    expected["traps"]["high_stakes_low_probability"] = "hepatic venous outflow obstruction"

    # Notes -----------------------------------------------------------------------------------
    templated_exam = ("General: No acute distress. Neuro: Alert and oriented x3. No asterixis. "
                      "Abdomen: Soft, mild right upper quadrant tenderness. Skin: Jaundice.")
    note(cn, "H&P by Dana Placeholder, MD at 3-3-2025 4-30 AM.pdf", P, "H&P", "3/3/2025 7:10 AM",
         "H&P by Dana Placeholder, MD at 3/3/2025 4:30 AM", [
             ("History of Present Illness", (
                 "61 year old admitted with three weeks of fatigue and five days of yellowing of the eyes and dark "
                 "urine. Started an over-the-counter turmeric and green tea extract supplement about six weeks ago. "
                 "Atorvastatin 20 mg daily started two months ago by outpatient physician. Reports one to two beers "
                 "per week. No travel. No prior liver disease known.")),
             ("Physical Exam", templated_exam),
             ("Medications", "Atorvastatin 20 mg daily (held). Supplement: turmeric with green tea extract (held)."),
             ("Assessment and Plan", (
                 "Acute hepatocellular liver injury. Leading consideration drug or supplement induced liver injury. "
                 "Check viral hepatitis panel, acetaminophen level, autoimmune markers, and ultrasound with Doppler. "
                 "Hold statin and supplement. Trend liver panel and INR daily.")),
         ])
    note(cn, "Pharmacy Note by Jamie Mockwell, PharmD at 3-4-2025 10-05 AM.pdf", P, "Pharmacy Note",
         "3/4/2025 10:20 AM", "Pharmacy Note by Jamie Mockwell, PharmD at 3/4/2025 10:05 AM", [
             ("Medication Reconciliation", (
                 "Atorvastatin held on admission. Supplement reported by family, not on home list, now documented. "
                 "Active orders include acetaminophen 650 mg by mouth every 6 hours as needed for pain or fever.")),
         ])
    note(cn, "Progress Notes by Dana Placeholder, MD at 3-4-2025 9-15 AM.pdf", P, "Progress Notes",
         "3/4/2025 5:40 PM", "Progress Notes by Dana Placeholder, MD at 3/4/2025 9:15 AM", [
             ("Interval History", "Fatigued. Tolerating diet. Family at bedside."),
             ("Physical Exam", templated_exam),
             ("Assessment and Plan", (
                 "Acute liver injury, drug or supplement induced remains leading. CT raised question of hepatic vein "
                 "flow. Ultrasound addendum reports patent hepatic veins, will not pursue further imaging. "
                 "Hepatology consulted.")),
         ])
    note(cn, "Consult Note by Morgan Examplename, MD at 3-4-2025 1-20 PM.pdf", P, "Consults",
         "3/4/2025 6:02 PM", "Consult Note by Morgan Examplename, MD at 3/4/2025 1:20 PM", [
             ("Reason for Consult", "Acute hepatocellular injury with rising bilirubin."),
             ("Assessment", (
                 "Pattern is hepatocellular. Drug or supplement induced injury is most likely given timing. "
                 "Autoimmune hepatitis remains on the differential with elevated IgG pending confirmation. ANA "
                 "negative does not exclude it. Will send smooth muscle antibody. Consider liver biopsy if bilirubin "
                 "continues to rise or autoimmune markers return positive.")),
         ])
    note(cn, "Progress Notes by Dana Placeholder, MD at 3-5-2025 8-50 AM.pdf", P, "Progress Notes",
         "3/5/2025 4:15 PM", "Progress Notes by Dana Placeholder, MD at 3/5/2025 8:50 AM", [
             ("Interval History", "More tired today per nursing."),
             ("Physical Exam", templated_exam),
             ("Assessment and Plan", (
                 "Bilirubin rising. Two ultrasounds confirmed hepatic vein patency. Continue supportive care. "
                 "Smooth muscle antibody pending.")),
         ])
    # Trap: the therapy note measures a finding the templated physician exam denies.
    note(cn, "Physical Therapy Evaluation by Riley Sampleton, PT at 3-5-2025 2-00 PM.pdf", P, "Therapy Evaluation",
         "3/5/2025 3:30 PM", "Physical Therapy Evaluation by Riley Sampleton, PT at 3/5/2025 2:00 PM", [
             ("Cognition", "Oriented to self and place, not to date or situation. Required repeated cues."),
             ("Observation", "Bilateral asterixis present with sustained wrist extension."),
             ("Mobility", "Moderate assist for bed to chair transfer. Ambulated 15 feet with rolling walker."),
         ])
    expected["traps"]["copy_forward_exam"] = ("Progress Notes say 'No asterixis', PT evaluation 3/5 documents "
                                              "bilateral asterixis")
    note(cn, "Nursing Note by Casey Demo, RN at 3-5-2025 11-40 PM.pdf", P, "Nursing Note", "3/6/2025 12:05 AM",
         "Nursing Note by Casey Demo, RN at 3/5/2025 11:40 PM", [
             ("Note", "Patient confused overnight, attempting to get out of bed without assistance. Bed alarm on. "
                      "Reoriented several times."),
         ])
    # Trap: leading space in the file name.
    note(cn, " Progress Notes by Dana Placeholder, MD at 3-6-2025 9-05 AM.pdf", P, "Progress Notes",
         "3/6/2025 3:55 PM", "Progress Notes by Dana Placeholder, MD at 3/6/2025 9:05 AM", [
             ("Interval History", "Nursing reports intermittent confusion overnight."),
             ("Physical Exam", templated_exam),
             ("Assessment and Plan", (
                 "Bilirubin 7.2 and INR 1.7. Started lactulose for possible mild hepatic encephalopathy. "
                 "Hepatology following.")),
         ])
    expected["traps"]["leading_space_filename"] = " Progress Notes by Dana Placeholder, MD at 3-6-2025 9-05 AM.pdf"
    note(cn, "Progress Notes by Morgan Examplename, MD at 3-6-2025 657 PM.pdf", P, "Progress Notes",
         "3/6/2025 7:30 PM", "Progress Notes by Morgan Examplename, MD at 3/6/2025 6:57 PM", [
             ("Assessment and Plan", (
                 "Worsening synthetic function. Smooth muscle antibody still pending. If positive, autoimmune "
                 "hepatitis moves up the differential and the team will discuss biopsy versus empiric therapy.")),
         ])
    note(cn, "Nutrition Note by Taylor Stubwell, RD at 3-5-2025 10-00 AM.pdf", P, "Nutrition Note",
         "3/5/2025 10:40 AM", "Nutrition Note by Taylor Stubwell, RD at 3/5/2025 10:00 AM", [
             ("Assessment", "Intake about 50 percent of meals. Albumin 3.1. Recommend oral supplement with meals."),
         ])
    note(cn, "Case Management Note by Sam Mockford, LCSW at 3-6-2025 11-30 AM.pdf", P, "Case Management",
         "3/6/2025 11:45 AM", "Case Management Note by Sam Mockford, LCSW at 3/6/2025 11:30 AM", [
             ("Note", "Anticipated length of stay uncertain pending workup. Lives with spouse. Home with support "
                      "anticipated."),
         ])
    # Trap: the newest result (send-out antibody, resulted 3/7 4:48 PM) is not absorbed by the newest note.
    note(cn, "Progress Notes by Dana Placeholder, MD at 3-7-2025 8-40 AM.pdf", P, "Progress Notes",
         "3/7/2025 5:20 PM", "Progress Notes by Dana Placeholder, MD at 3/7/2025 8:40 AM", [
             ("Physical Exam", templated_exam),
             ("Assessment and Plan", "Smooth muscle antibody pending. Continue lactulose. Trend labs."),
         ])
    expected["traps"]["unabsorbed_result"] = "Miscellaneous Send Out Test.pdf resulted after last note says pending"

    with open(os.path.join(root, "family-recap.md"), "w") as fh:
        fh.write(textwrap.dedent("""\
            # Family recap (fictional fixture)

            Written by Alex's spouse from memory of conversations. Contains interpretation on purpose.

            - Alex started the turmeric supplement "maybe a month or two ago." We think the supplement is
              definitely what caused this, because a neighbor had the same thing.
            - The doctor told us on 3/4 that the scan showed a possible clot, but the ultrasound doctor said no
              clot, so that is ruled out and we can stop worrying about it.
            - Alex has seemed "foggy" since 3/5 and was shaking his hands when he held them up. The morning doctor
              said he was fine and sharp.
            - Alex's mother had "some liver thing" and thyroid disease. His sister has lupus.
            - Alex took ibuprofen most days for back pain before admission. We did not tell anyone this yet.
            """))
    os.makedirs(os.path.join(root, "prior"))
    with open(os.path.join(root, "prior", "family-analysis.md"), "w") as fh:
        fh.write(textwrap.dedent("""\
            # Prior family analysis (fictional fixture)

            Bilirubin has been trending down since admission, which means the liver is recovering.
            Two separate ultrasounds confirmed the hepatic veins are open, so a clot is ruled out.
            The autoimmune testing was all negative.
            """))
    expected["traps"]["prior_contradicted"] = [
        "bilirubin trending down (records show 3.8 -> 4.6 -> 5.9 -> 7.2)",
        "two separate ultrasounds (one ultrasound plus a non-independent addendum)",
        "autoimmune testing all negative (smooth muscle antibody 38 High, IgG 1890 High)",
    ]
    expected["counts"] = {"results": len(os.listdir(tr)), "notes": len(os.listdir(cn))}
    expected["identifiers"] = ["Alex Fixture", "2/14/1963", "99900001", "Example General Hospital",
                               "Dana Placeholder", "Morgan Examplename"]
    expected["family_report_unshared_history"] = "daily ibuprofen before admission"
    return expected


# ---------------------------------------------------------------------------------------------
# Case B: community-acquired pneumonia, team is right. Fictional patient "Robin Sample"
# ---------------------------------------------------------------------------------------------

B_PATIENT = {
    "header": "Name: Robin Sample | DOB: 7/9/1979 | MRN: 99900002 | Example Community Hospital",
    "attending": "Lee Testperson, MD",
    "lab": "Example Community Lab",
}


def build_case_b(root):
    tr = os.path.join(root, "Test Results")
    cn = os.path.join(root, "Care Team Notes")
    os.makedirs(tr)
    os.makedirs(cn)
    P = B_PATIENT
    expected = {"labs": [], "traps": {}}
    cbc_refs = [
        ("WBC", "4.0 - 10.5", "K/uL", 4.0, 10.5), ("Hemoglobin", "12.0 - 16.0", "g/dL", 12, 16),
        ("Platelet Count", "150 - 400", "K/uL", 150, 400), ("Abs Neut", "1.8 - 7.7", "K/uL", 1.8, 7.7),
    ]
    for fname, coll, res, vals in [
        ("Complete Blood Count with Differential.pdf", "Nov 12, 2024 9:40 PM", "Nov 12, 2024 10:10 PM",
         ["16.8", "13.9", "265", "14.1"]),
        ("Complete Blood Count with Differential 2.pdf", "Nov 14, 2024 6:00 AM", "Nov 14, 2024 6:30 AM",
         ["11.2", "13.4", "281", "8.6"]),
        ("Complete Blood Count with Differential 3.pdf", "Nov 15, 2024 6:10 AM", "Nov 15, 2024 6:38 AM",
         ["8.1", "13.2", "302", "5.4"]),
    ]:
        rows = [(n, v, flag(v, lo, hi), ref, u, lo, hi) for (n, ref, u, lo, hi), v in zip(cbc_refs, vals)]
        result(tr, fname, P, "Complete Blood Count with Differential", coll, res, two_col=rows)
        expected["labs"] += [{"file": fname, "analyte": r[0], "value": r[1]} for r in rows]
    for fname, coll, res, crp in [
        ("C-Reactive Protein.pdf", "Nov 12, 2024 9:40 PM", "Nov 12, 2024 10:30 PM", "182"),
        ("C-Reactive Protein 2.pdf", "Nov 15, 2024 6:10 AM", "Nov 15, 2024 7:00 AM", "41"),
    ]:
        rows = [("CRP", crp, "High", "0 - 10", "mg/L", 0, 10)]
        result(tr, fname, P, "C-Reactive Protein", coll, res, analytes=rows)
        expected["labs"] += [{"file": fname, "analyte": "CRP", "value": crp}]
    rows = [("Procalcitonin", "2.4", "High", "0.00 - 0.49", "ng/mL", 0, 0.49)]
    result(tr, "Procalcitonin.pdf", P, "Procalcitonin", "Nov 12, 2024 9:40 PM", "Nov 12, 2024 11:15 PM", analytes=rows)
    expected["labs"].append({"file": "Procalcitonin.pdf", "analyte": "Procalcitonin", "value": "2.4"})
    result(tr, "Streptococcus pneumoniae Antigen, Urine.pdf", P, "Streptococcus pneumoniae Antigen, Urine",
           "Nov 12, 2024 10:05 PM", "Nov 13, 2024 8:20 AM", body="S. pneumoniae Urinary Antigen: Positive (A)")
    result(tr, "Blood Culture.pdf", P, "Blood Culture", "Nov 12, 2024 9:45 PM", "Nov 17, 2024 10:00 PM",
           body="Final: No growth at 5 days.")
    result(tr, "XR Chest 2 Views.pdf", P, "XR Chest 2 Views", "Nov 12, 2024 9:15 PM", "Nov 12, 2024 9:58 PM",
           body=("IMPRESSION:\nRight lower lobe consolidation consistent with pneumonia. No pleural effusion.\n\n"
                 "NARRATIVE:\nExam performed: 11/12/2024 9:32 PM."))
    result(tr, "XR Chest 2 Views 2.pdf", P, "XR Chest 2 Views", "Nov 15, 2024 8:00 AM", "Nov 15, 2024 9:10 AM",
           body=("IMPRESSION:\nImproving right lower lobe consolidation.\n\nNARRATIVE:\nExam performed: 11/15/2024 8:21 AM."))

    note(cn, "ED Provider Note by Lee Testperson, MD at 11-12-2024 9-05 PM.pdf", P, "ED Provider Notes",
         "11/12/2024 11:50 PM", "ED Provider Note by Lee Testperson, MD at 11/12/2024 9:05 PM", [
             ("History", "45 year old with four days of productive cough, fever to 102.4 F, and right sided "
                         "pleuritic chest pain. Nonsmoker. No recent travel or hospitalization."),
             ("Assessment and Plan", "Community-acquired pneumonia, right lower lobe. Blood cultures, urinary "
                                     "antigens, start ceftriaxone and azithromycin. Admit to medicine."),
         ])
    for day, text in [
        ("11-13-2024 8-30 AM", "Febrile overnight to 101.1 F. Urinary pneumococcal antigen positive. Continue therapy."),
        ("11-14-2024 8-45 AM", "Afebrile for 18 hours. WBC down to 11.2. Tolerating diet. Plan oral step-down tomorrow."),
        ("11-15-2024 9-00 AM", "Afebrile 42 hours. Repeat film improving. Transition to oral amoxicillin. "
                               "Discharge planned today with follow-up in one week."),
    ]:
        shown = day.replace("-", "/", 2).replace("-", ":")
        note(cn, f"Progress Notes by Lee Testperson, MD at {day}.pdf", P, "Progress Notes", shown,
             f"Progress Notes by Lee Testperson, MD at {shown}", [
                 ("Physical Exam", "Alert and oriented. Crackles right base, improving."),
                 ("Assessment and Plan", f"Pneumococcal community-acquired pneumonia. {text}"),
             ])
    note(cn, "Nursing Note by Jesse Fakename, RN at 11-14-2024 3-00 AM.pdf", P, "Nursing Note",
         "11/14/2024 3:20 AM", "Nursing Note by Jesse Fakename, RN at 11/14/2024 3:00 AM", [
             ("Note", "Resting comfortably. Temp 98.9 F. Oxygen saturation 96 percent on room air."),
         ])
    with open(os.path.join(root, "family-recap.md"), "w") as fh:
        fh.write("# Family recap (fictional fixture)\n\nRobin got sick after a cold went around the office. "
                 "Doctors said pneumonia on the right side and started IV antibiotics. Robin feels much better.\n")
    expected["traps"]["team_is_right"] = "pneumococcal community-acquired pneumonia, improving on therapy"
    expected["counts"] = {"results": len(os.listdir(tr)), "notes": len(os.listdir(cn))}
    expected["identifiers"] = ["Robin Sample", "7/9/1979", "99900002", "Example Community Hospital", "Lee Testperson"]
    return expected


def main():
    for name, build in [("case-a", build_case_a), ("case-b", build_case_b)]:
        root = os.path.join(HERE, name)
        if os.path.exists(root):
            shutil.rmtree(root)
        os.makedirs(root)
        expected = build(root)
        with open(os.path.join(root, "expected.json"), "w") as fh:
            json.dump(expected, fh, indent=2)
            fh.write("\n")
        print(f"{name}: {expected['counts']['results']} results, {expected['counts']['notes']} notes, "
              f"{len(expected['labs'])} seeded lab values")


if __name__ == "__main__":
    main()
