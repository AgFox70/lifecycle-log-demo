"""Fictional document text used by the scenario builder."""
BODY = {
 "change-control": ["Requested by", "Description of the change", "Reason", "Impact (low / medium / high)", "Verification"],
 "incident": ["Reported by", "What happened", "Severity (low / medium / high)", "Immediate action"],
 "risk": ["Hazard", "Cause", "Harm", "Controls"],
 "deviation": ["Requirement deviated from", "Description", "Interim controls"],
 "capa": ["Source", "Problem statement", "Containment"],
 "supplier": ["Supplier name", "Service provided", "Criticality", "Findings"],
}
DOCS = {
 "SOP-014": ("Data Retention and Archiving", "sop", "CC-001", ["Draft"],
   ["## 1 Purpose\n\nSet how long study and quality records are kept and how they are archived.", "## 2 Scope\n\nAll controlled records created by Northwind Labs staff.",
    "## 3 Procedure\n\n1. Classify the record against the retention schedule (REC-052).\n2. Keep active records in the working folder until the study is closed.\n3. Move closed records to the archive within 30 days, following WI-031.\n4. Destroy records only after the retention period and with Quality approval.",
    "## 4 Responsibilities\n\nRecord owners classify and archive. Quality approves destruction."]),
 "WI-031": ("Archiving a Closed Study Folder", "wi", "CC-001", ["Draft"],
   ["## Steps\n\n1. Confirm the study is closed in the log.\n2. Check the folder against the archive checklist.\n3. Compress the folder and record its checksum.\n4. Move it to the archive share and add an entry to the archive log (REC-053).\n5. Remove the working copy only after the checksum is verified."]),
 "REC-052": ("Retention Schedule", "rec", "CC-001", ["Draft", "Approved"],
   ["| Record type | Retention | Trigger |\n|---|---|---|\n| Study record | 10 years | Study close |\n| Supplier file | 6 years | Contract end |\n| Training record | 6 years | Staff departure |\n| Incident record | 10 years | Incident close |"]),
 "SOP-015": ("Supplier Qualification", "sop", "CC-002", ["Draft"],
   ["## 1 Purpose\n\nDecide whether a supplier is fit to provide a service to Northwind Labs.", "## 2 Procedure\n\n1. Send the supplier questionnaire (WI-032).\n2. Score the answers against the evaluation criteria.\n3. Record the decision in a Supplier Evaluation record.\n4. Re-evaluate every 24 months or after a serious incident."]),
 "WI-032": ("Completing the Supplier Questionnaire", "wi", "CC-002", ["Draft"],
   ["## Steps\n\n1. Open the questionnaire template.\n2. Fill in the supplier details and service description.\n3. Attach the supplier certificates.\n4. Send it to the supplier contact and log the date."]),
 "SOP-016": ("Document Archiving", "sop", "CC-003", ["Draft", "Approved"],
   ["## 1 Purpose\n\nKeep superseded documents retrievable.", "## 2 Procedure\n\n1. Mark the old version as superseded.\n2. Move it to the archive folder.\n3. Log the move in REC-053."]),
 "REC-053": ("Archive Log", "rec", "CC-003", ["Draft", "Approved"],
   ["| Date | Item | Moved by |\n|---|---|---|\n| 2026-09-12 | Old form set v2 | A. Author |"]),
 "SOP-017": ("Training and Competence", "sop", "", ["Draft"],
   ["## 1 Purpose\n\nShow that staff are trained before they do controlled work.", "## 2 Procedure\n\n1. Line manager assigns training from the matrix (REC-054).\n2. Trainee reads and signs the document.\n3. Competence is confirmed by the line manager."]),
}
