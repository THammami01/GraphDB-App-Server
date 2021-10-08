# from typing import Union
from .models import MedicalRecordModel, FileModel, IDOnlyModel, ExcelNodeModel
from datetime import datetime
import json


def query_add_medical_record(session, mr: MedicalRecordModel):
    # TODO: YOU CAN ACCEPT MR NAME AS WELL

    query = """
        CREATE(m: MedicalRecord {name: "MR-%s", uuid: "%s", created_at: "%s"})
        CREATE(p: Patient {firstname: "%s", lastname: "%s", nic_nb: "%s", email: "%s", phone_nb: "%s", birthday: "%s"})
        CREATE(md: Docs { name: "Docs",  uuid: "%s"})
        CREATE(mm: Media { name: "Media", uuid: "%s" })
        CREATE (p)-[:HAS]->(m)
        CREATE (m)-[:CONTAINS_DOCS]->(md)
        CREATE (m)-[:CONTAINS_MEDIA]->(mm)
    """ % (mr.uuid, mr.uuid, mr.created_at, mr.firstname, mr.lastname, mr.nic_nb, mr.email, mr.phone_nb, mr.birthday, mr.uuid, mr.uuid)
    session.run(query=query)


# Union[FileModel, dict]
def query_add_file(session, file: FileModel, fromComposedFile: bool = False):
    # YOU CAN REMOVE TYPE SINCE IT IS KNOWN FROM FILE FORMAT

    file_cat = None
    if(fromComposedFile):
        pass
    elif(file.format in ("IMG", "AUD", "VID")):
        file_cat = "Media"
    else:
        file_cat = "Docs"

    query = """
        MATCH(n%s) WHERE n.uuid = "%s"
        CREATE(p: %sFile {name: "%s", uuid: "%s", path: "%s", type: "%s", added_at: "%s"})
        CREATE(n)-[r:CONTAINS_%s]->(p)
    """ % ("" if fromComposedFile else f": {file_cat}", file.parent_uuid, file.format, file.name, file.uuid, file.path, file.type, str(datetime.now()).split(".")[0][:-3], file.format)

    session.run(query=query)


def query_update_medical_record(session, mr: MedicalRecordModel):
    # YOU CAN ACCEPT MR NAME AS WELL
    query = """
        MATCH (p:Patient)-[:HAS]->(m:MedicalRecord {uuid: "%s"})
        SET p.firstname = "%s", p.lastname = "%s", p.nic_nb = "%s", p.email = "%s",
            p.phone_nb = "%s", p.birthday = "%s"
    """ % (mr.uuid, mr.firstname, mr.lastname, mr.nic_nb, mr.email, mr.phone_nb, mr.birthday)
    session.run(query=query)


def query_update_file(session, file: FileModel):  # Unused
    query = """
        MATCH (f {uuid: "%s"})
        SET f.name = "%s"
    """ % (file.uuid, file.name)
    session.run(query=query)


def query_mr_nodes_contained_files_uuids(session, uuid: str) -> list[str]:
    query = """
        MATCH(m {uuid: "%s"})-[]->(n)-[]->(o)-[]->(p)
        RETURN p;
    """ % (uuid,)
    nodes = session.run(query=query)
    list1 = [node['p'].get("uuid") for node in nodes]

    query = """
        MATCH(m {uuid: "%s"})-[]->(n)-[]->(o)
        RETURN o;
    """ % (uuid,)
    nodes = session.run(query=query)
    list2 = [node['o'].get("uuid") for node in nodes]

    # query = """
    #     MATCH(m {uuid: "%s"})-[]->(n)
    #     RETURN n;
    # """ % (uuid,)
    # nodes = session.run(query=query)
    # list3 = [node['n'].get("uuid") for node in nodes]

    final_list = list(filter(lambda n: n is not None,
                      list(set(list1 + list2))))
    # final_list = list(set(list1 + list2 + list3)).remove(None)

    print(final_list)
    return list(final_list)


def query_node_contained_files_uuids(session, uuid: str) -> list[str]:
    query = """
        MATCH(m {uuid: "%s"})-[]->(n)-[]->(o)-[]->(p)
        RETURN p;
    """ % (uuid,)
    nodes = session.run(query=query)
    list1 = [node['p'].get("uuid") for node in nodes]

    query = """
        MATCH(m {uuid: "%s"})-[]->(n)-[]->(o)
        RETURN o;
    """ % (uuid,)
    nodes = session.run(query=query)
    list2 = [node['o'].get("uuid") for node in nodes]

    query = """
        MATCH(m {uuid: "%s"})-[]->(n)
        RETURN n;
    """ % (uuid,)
    nodes = session.run(query=query)
    list3 = [node['n'].get("uuid") for node in nodes]

    print("BRY0001")
    final_list = list(filter(lambda n: n is not None,
                      list(set(list1 + list2 + list3))))
    # final_list = list(set(list1 + list2 + list3)).remove(None)

    print(final_list)
    return list(final_list)


def query_get_contained_files(session, obj: IDOnlyModel):
    query = """
        MATCH(m {uuid: "%s"})-[]->(n)
        RETURN n;
    """ % (obj.uuid,)
    nodes = session.run(query=query)

    list1 = [dict(node['n'].items()) for node in nodes]
    list1 = list(filter(lambda n:
                        n["name"] not in ("Docs", "Media")
                        and n["type"] != "stat", list1))

    return list1


# TODO: FIX DELETE MR
def query_delete_medical_record(session, mr_uuid: str):
    print("STARTING DELETE MR QUERY")

    query = """
        MATCH(p:Patient)-[:HAS]->(m: MedicalRecord {uuid: "%s"})-[]->(n)-[]->(o)-[]->(q)-[]->(r)
        DETACH DELETE r;
    """ % (mr_uuid,)
    session.run(query=query)

    query = """
        MATCH(p:Patient)-[:HAS]->(m: MedicalRecord {uuid: "%s"})-[]->(n)-[]->(o)-[]->(q)
        DETACH DELETE q;
    """ % (mr_uuid,)
    session.run(query=query)

    query = """
        MATCH(p:Patient)-[:HAS]->(m: MedicalRecord {uuid: "%s"})-[]->(n)-[]->(o)
        DETACH DELETE o;
    """ % (mr_uuid,)
    session.run(query=query)

    query = """
        MATCH(p:Patient)-[:HAS]->(m:MedicalRecord {uuid: "%s"})-[]->(n)
        DETACH DELETE n;
    """ % (mr_uuid,)
    session.run(query=query)

    query = """
        MATCH(p:Patient)-[:HAS]->(m:MedicalRecord {uuid: "%s"})
        DETACH DELETE p;
    """ % (mr_uuid,)
    session.run(query=query)

    query = """
        MATCH(m:MedicalRecord {uuid: "%s"})
        DETACH DELETE m;
    """ % (mr_uuid,)
    session.run(query=query)

    print("FINISHING DELETE MR QUERY")


def query_delete_file(session, delNode: IDOnlyModel):
    query = """
        MATCH(m {uuid: "%s"})-[]->(n)-[]->(o)
        DETACH DELETE o;
    """ % (delNode.uuid)
    session.run(query=query)

    query = """
        MATCH(m {uuid: "%s"})-[]->(n)
        DETACH DELETE n;
    """ % (delNode.uuid)
    session.run(query=query)

    query = """
        MATCH(m {uuid: "%s"})
        DETACH DELETE m;
    """ % (delNode.uuid,)
    session.run(query=query)


def query_get_medical_records(session):
    query = """
        MATCH(p:Patient)-[:HAS]->(m: MedicalRecord)
        RETURN p, m;
    """
    nodes = session.run(query=query)

    res_list = [{"patient": dict(node['p'].items()), "medicalRecord": dict(
        node['m'].items())} for node in nodes]

    return res_list


# with open("./definitions.json", "r") as f:
#     dictionnary = json.load(f)

dictionnary = {
  "AI/RHEUM": "AIR",
  "Alternative Billing Concepts": "ALT",
  "Alcohol and Other Drug Thesaurus": "AOD",
  "Authorized Osteopathic Thesaurus": "AOT",
  "Anatomical Therapeutic Chemical Classification System": "ATC",
  "Beth Israel Problem List": "BI",
  "Clinical Care Classification": "CCC",
  "Clinical Problem Statements": "CCPSS",
  "Clinical Classifications Software Refined for ICD-10-CM": "CCSR_ICD10CM",
  "Clinical Classifications Software Refined for ICD-10-PCS": "CCSR_ICD10PCS",
  "Clinical Classifications Software": "CCS",
  "CDT": "CDT",
  "Consumer Health Vocabulary": "CHV",
  "COSTAR": "COSTAR",
  "Medical Entities Dictionary": "CPM",
  "CPT Spanish": "CPTSP",
  "CPT - Current Procedural Terminology": "CPT",
  "CRISP Thesaurus": "CSP",
  "COSTART": "CST",
  "Vaccines Administered": "CVX",
  "Diseases Database": "DDB",
  "ICD-10 German": "DMDICD10",
  "UMDNS German": "DMDUMD",
  "DrugBank": "DRUGBANK",
  "Diagnostic and Statistical Manual of Mental Disorders, Fifth Edition": "DSM-5",
  "DXplain": "DXP",
  "Foundational Model of Anatomy": "FMA",
  "Gene Ontology": "GO",
  "Gold Standard Drug Database": "GS",
  "CDT in HCPCS": "HCDT",
  "HCPCS - Healthcare Common Procedure Coding System": "HCPCS",
  "CPT in HCPCS": "HCPT",
  "HUGO Gene Nomenclature Committee": "HGNC",
  "HL7 Version 2.5": "HL7V2.5",
  "HL7 Version 3.0": "HL7V3.0",
  "ICPC2E ICD10 Relationships": "HLREL",
  "Human Phenotype Ontology": "HPO",
  "ICD-10, American English Equivalents": "ICD10AE",
  "ICD-10, Australian Modification, Americanized English Equivalents": "ICD10AMAE",
  "ICD-10, Australian Modification": "ICD10AM",
  "International Classification of Diseases, Tenth Revision, Clinical Modification": "ICD10CM",
  "ICD10, Dutch Translation": "ICD10DUT",
  "ICD-10 Procedure Coding System": "ICD10PCS",
  "International Classification of Diseases and Related Health Problems, Tenth Revision": "ICD10",
  "International Classification of Diseases, Ninth Revision, Clinical Modification": "ICD9CM",
  "International Classification of Functioning, Disability and Health for Children and Youth": "ICF-CY",
  "International Classification of Functioning, Disability and Health": "ICF",
  "International Classification for Nursing Practice": "ICNP",
  "ICPC2E Dutch": "ICPC2EDUT",
  "International Classification of Primary Care, 2nd Edition, Electronic": "ICPC2EENG",
  "ICPC2-ICD10 Thesaurus, Dutch Translation": "ICPC2ICD10DUT",
  "ICPC2-ICD10 Thesaurus": "ICPC2ICD10ENG",
  "ICPC-2 PLUS": "ICPC2P",
  "ICPC Basque": "ICPCBAQ",
  "ICPC Danish": "ICPCDAN",
  "ICPC Dutch": "ICPCDUT",
  "ICPC Finnish": "ICPCFIN",
  "ICPC French": "ICPCFRE",
  "ICPC German": "ICPCGER",
  "ICPC Hebrew": "ICPCHEB",
  "ICPC Hungarian": "ICPCHUN",
  "ICPC Italian": "ICPCITA",
  "ICPC Norwegian": "ICPCNOR",
  "ICPC Portuguese": "ICPCPOR",
  "ICPC Spanish": "ICPCSPA",
  "ICPC Swedish": "ICPCSWE",
  "International Classification of Primary Care": "ICPC",
  "Congenital Mental Retardation Syndromes": "JABL",
  "Korean Standard Classification of Disease Version 5": "KCD5",
  "Library of Congress Subject Headings, Northwestern University subset": "LCH_NW",
  "Library of Congress Subject Headings": "LCH",
  "LOINC Linguistic Variant - German, Austria": "LNC-DE-AT",
  "LOINC Linguistic Variant - German, Germany": "LNC-DE-DE",
  "LOINC Linguistic Variant - Greek, Greece": "LNC-EL-GR",
  "LOINC Linguistic Variant - Spanish, Argentina": "LNC-ES-AR",
  "LOINC Linguistic Variant - Spanish, Spain": "LNC-ES-ES",
  "LOINC Linguistic Variant - Estonian, Estonia": "LNC-ET-EE",
  "LOINC Linguistic Variant - French, Belgium": "LNC-FR-BE",
  "LOINC Linguistic Variant - French, Canada": "LNC-FR-CA",
  "LOINC Linguistic Variant - French, France": "LNC-FR-FR",
  "LOINC Linguistic Variant - Italian, Italy": "LNC-IT-IT",
  "LOINC Linguistic Variant - Korea, Korean": "LNC-KO-KR",
  "LOINC Linguistic Variant - Dutch, Netherlands": "LNC-NL-NL",
  "LOINC Linguistic Variant - Portuguese, Brazil": "LNC-PT-BR",
  "LOINC Linguistic Variant - Russian, Russia": "LNC-RU-RU",
  "LOINC Linguistic Variant - Turkish, Turkey": "LNC-TR-TR",
  "LOINC Linguistic Variant - Chinese, China": "LNC-ZH-CN",
  "LOINC": "LNC",
  "Glossary of Clinical Epidemiologic Terms": "MCM",
  "MedDRA Brazilian Portuguese": "MDRBPO",
  "MedDRA Czech": "MDRCZE",
  "MedDRA Dutch": "MDRDUT",
  "MedDRA French": "MDRFRE",
  "MedDRA German": "MDRGER",
  "MedDRA Hungarian": "MDRHUN",
  "MedDRA Italian": "MDRITA",
  "MedDRA Japanese": "MDRJPN",
  "MedDRA Korean": "MDRKOR",
  "MedDRA Portuguese": "MDRPOR",
  "MedDRA Russian": "MDRRUS",
  "MedDRA Spanish": "MDRSPA",
  "MedDRA": "MDR",
  "Medication Reference Terminology": "MED-RT",
  "MEDCIN": "MEDCIN",
  "MEDLINEPLUS Spanish": "MEDLINEPLUS_SPA",
  "MedlinePlus Health Topics": "MEDLINEPLUS",
  "Multum": "MMSL",
  "Micromedex": "MMX",
  "MeSH Czech": "MSHCZE",
  "MeSH Dutch": "MSHDUT",
  "MeSH Finnish": "MSHFIN",
  "MeSH French": "MSHFRE",
  "MeSH German": "MSHGER",
  "MeSH Italian": "MSHITA",
  "MeSH Japanese": "MSHJPN",
  "MeSH Latvian": "MSHLAV",
  "MeSH Norwegian": "MSHNOR",
  "MeSH Polish": "MSHPOL",
  "MeSH Portuguese": "MSHPOR",
  "MeSH Russian": "MSHRUS",
  "MeSH Croatian": "MSHSCR",
  "MeSH Spanish": "MSHSPA",
  "MeSH Swedish": "MSHSWE",
  "MeSH": "MSH",
  "Metathesaurus CMS Formulary Reference File": "MTHCMSFRF",
  "ICD-9-CM Entry Terms": "MTHICD9",
  "ICPC2E American English Equivalents": "MTHICPC2EAE",
  "ICPC2E-ICD10 Thesaurus, American English Equivalents": "MTHICPC2ICD10AE",
  "Minimal Standard Terminology French (UMLS)": "MTHMSTFRE",
  "Minimal Standard Terminology Italian (UMLS)": "MTHMSTITA",
  "Minimal Standard Terminology (UMLS)": "MTHMST",
  "FDA Structured Product Labels": "MTHSPL",
  "Metathesaurus Names": "MTH",
  "Manufacturers of Vaccines": "MVX",
  "NANDA-I Taxonomy": "NANDA-I",
  "NCBI Taxonomy": "NCBI",
  "NCI SEER ICD Mappings": "NCISEER",
  "American College of Cardiology/American Heart Association Clinical Data Terminology": "NCI_ACC-AHA",
  "Biomedical Research Integrated Domain Group Model, 3.0.3": "NCI_BRIDG_3_0_3",
  "Biomedical Research Integrated Domain Group Model, 5.3": "NCI_BRIDG_5_3",
  "Biomedical Research Integrated Domain Group Model Subset": "NCI_BRIDG",
  "BioCarta online maps of molecular pathways, adapted for NCI use": "NCI_BioC",
  "Chemical Biology and Drug Development Vocabulary": "NCI_CBDD",
  "U.S. Centers for Disease Control and Prevention Terms": "NCI_CDC",
  "CDISC Glossary Terminology": "NCI_CDISC-GLOSS",
  "CDISC Terminology": "NCI_CDISC",
  "Cellosaurus": "NCI_CELLOSAURUS",
  "Cancer Research Center of Hawaii Nutrition Terminology": "NCI_CRCH",
  "Common Terminology Criteria for Adverse Events 3.0": "NCI_CTCAE_3",
  "Common Terminology Criteria for Adverse Events 5.0": "NCI_CTCAE_5",
  "Common Terminology Criteria for Adverse Events 4.3 Subset": "NCI_CTCAE",
  "Clinical Trial Data Commons": "NCI_CTDC",
  "Cancer Therapy Evaluation Program - Simple Disease Classification": "NCI_CTEP-SDC",
  "Clinical Trials Reporting Program Terms": "NCI_CTRP",
  "Content Archive Resource Exchange Lexicon": "NCI_CareLex",
  "NCI Division of Cancer Prevention Program Terms": "NCI_DCP",
  "Digital Imaging Communications in Medicine Terms": "NCI_DICOM",
  "NCI Developmental Therapeutics Program": "NCI_DTP",
  "European Directorate for the Quality of Medicines & Healthcare Terms": "NCI_EDQM-HC",
  "FDA Terminology": "NCI_FDA",
  "Global Alignment of Immunization Safety Assessment in Pregnancy Terms": "NCI_GAIA",
  "NCI Genomic Data Commons Terms": "NCI_GDC",
  "Geopolitical Entities, Names, and Codes (GENC) Standard Edition 1": "NCI_GENC",
  "NCI Integrated Canine Data Commons Terms": "NCI_ICDC",
  "International Conference on Harmonization Terms": "NCI_ICH",
  "International Neonatal Consortium": "NCI_INC",
  "Jackson Laboratories Mouse Terminology, adapted for NCI use": "NCI_JAX",
  "KEGG Pathway Database Terms": "NCI_KEGG",
  "NCI Dictionary of Cancer Terms": "NCI_NCI-GLOSS",
  "NCI HUGO Gene Nomenclature": "NCI_NCI-HGNC",
  "NCI Health Level 7": "NCI_NCI-HL7",
  "NCPDP Terminology": "NCI_NCPDP",
  "NICHD Terminology": "NCI_NICHD",
  "Pediatric Cancer Data Commons": "NCI_PCDC",
  "Prostate Imaging Reporting and Data System Terms": "NCI_PI-RADS",
  "National Cancer Institute Nature Pathway Interaction Database Terms": "NCI_PID",
  "Registry Nomenclature Information System": "NCI_RENI",
  "Unified Code for Units of Measure": "NCI_UCUM",
  "Zebrafish Model Organism Database Terms": "NCI_ZFin",
  "Cancer Data Standards Registry and Repository": "NCI_caDSR",
  "NCI Thesaurus": "NCI",
  "FDB MedKnowledge": "NDDF",
  "Neuronames Brain Hierarchy": "NEU",
  "Nursing Interventions Classification": "NIC",
  "Nursing Outcomes Classification": "NOC",
  "National Uniform Claim Committee - Health Care Provider Taxonomy": "NUCCHCPT",
  "Online Mendelian Inheritance in Man": "OMIM",
  "Omaha System": "OMS",
  "Patient Care Data Set": "PCDS",
  "Physician Data Query": "PDQ",
  "Perioperative Nursing Data Set": "PNDS",
  "Pharmacy Practice Activity Classification": "PPAC",
  "Psychological Index Terms": "PSY",
  "Quick Medical Reference": "QMR",
  "Clinical Concepts by R A Miller": "RAM",
  "Read Codes Am Engl": "RCDAE",
  "Read Codes Am Synth": "RCDSA",
  "Read Codes Synth": "RCDSY",
  "Read Codes": "RCD",
  "RXNORM": "RXNORM",
  "SNOMED CT Spanish Edition": "SCTSPA",
  "SNOMED Intl 1998": "SNMI",
  "SNOMED 1982": "SNM",
  "SNOMED CT, US Edition": "SNOMEDCT_US",
  "SNOMED CT, Veterinary Extension": "SNOMEDCT_VET",
  "Source of Payment Typology": "SOP",
  "Standard Product Nomenclature": "SPN",
  "Source Terminology Names (UMLS)": "SRC",
  "Traditional Korean Medical Terms": "TKMT",
  "UltraSTAR": "ULT",
  "UMDNS": "UMD",
  "USP Model Guidelines": "USPMG",
  "USP Compendial Nomenclature": "USP",
  "Digital Anatomist": "UWDA",
  "National Drug File": "VANDF",
  "WHOART French": "WHOFRE",
  "WHOART German": "WHOGER",
  "WHOART Portuguese": "WHOPOR",
  "WHOART Spanish": "WHOSPA",
  "WHOART": "WHO"
}

def query_add_definitions(session, text_node_uuid: str, text_node_content: str):

    def fix_text(text: str):
        return " ".join(text.lower().split())

    fixed_text = fix_text(text_node_content)

    for voc in dictionnary:
        if fix_text(voc) in fixed_text:
            query = """
                MATCH(n) WHERE n.uuid = "%s"
                CREATE(v: Annotation {name: "%s", abbreviation: "%s"})
                CREATE(n)-[r:CONTAINS_VOC]->(v)
            """ % (text_node_uuid, voc, dictionnary[voc])
            session.run(query)


def query_add_excel_node(session, node: ExcelNodeModel, relation_name: str):
    # YOU CAN REMOVE TYPE SINCE IT IS KNOWN FROM FILE FORMAT
    query = """
        MATCH(ex: MS_XLSXFile) WHERE ex.uuid = "%s"
        CREATE(n: %s {name: "%s", value: "%s", type: "stat"})
        CREATE(ex)-[r:%s]->(n)
    """ % (node.parent_uuid, node.name, node.value, node.value, relation_name)
    session.run(query=query)
