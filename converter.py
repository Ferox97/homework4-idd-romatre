import os
import xml.etree.ElementTree as ET
import json

def extract_figures(root, pmcid):
    figures = []
    for fig in root.findall(".//fig"):
        fig_id = fig.get('id')
        caption_element = fig.find(".//caption")
        caption = ''.join(caption_element.itertext()).strip() if caption_element is not None else ""

        graphic_element = fig.find(".//graphic")
        href = graphic_element.get('{http://www.w3.org/1999/xlink}href') if graphic_element is not None else ""
        src = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/bin/{href}.jpg"

        paragraphs = extract_paragraphs_and_citations(root, fig_id, 'fig')

        figures.append({
            "fig_id": fig_id,
            "src": src,
            "caption": caption,
            "paragraphs": paragraphs
        })

    return figures

def extract_cell_content_and_paragraphs(root, tbody_element):
    cells = []
    processed_cell_contents = set()

    # Estrai il contenuto di ogni cella
    for cell in tbody_element.findall(".//td"):
        cell_text = ''.join(cell.itertext()).strip()
        if cell_text and cell_text not in processed_cell_contents:  # Processa solo se il contenuto è nuovo
            processed_cell_contents.add(cell_text)
            new_cell = {"content": cell_text, "cited_in": []}

            # Trova paragrafi che citano il contenuto di questa cella
            for p in root.findall(".//p"):
                paragraph_text = ''.join(p.itertext()).strip()
                if cell_text in paragraph_text:
                    new_cell["cited_in"].append(paragraph_text)

            cells.append(new_cell)

    return cells


def extract_citations(root, citation_ids):
    citations = []
    for citation_id in citation_ids:
        ref_element = root.find(f".//ref[@id='{citation_id}']")
        if ref_element is not None:
            citations.append(ET.tostring(ref_element, encoding='unicode', method='xml').strip())
    return citations

def extract_paragraphs_and_citations(root, id, ref_type):
    paragraphs = []
    for p in root.findall(".//p"):
        # Cerca riferimenti alle figure o tabelle in questo paragrafo
        refs = [xref for xref in p.findall(f".//xref[@ref-type='{ref_type}']") if xref.get('rid') == id]
        
        if refs:
            # Estrai il testo del paragrafo
            text = ''.join(p.itertext()).strip()

            # Estrai le citazioni bibliografiche, se presenti
            citation_ids = [xref.get('rid') for xref in p.findall(".//xref[@ref-type='bibr']")]
            citations = extract_citations(root, citation_ids)

            paragraphs.append({
                "cited_in": text,
                "citations": citations
            })

    return paragraphs


def extract_tables(root):
    tables = []
    for table_wrap in root.findall(".//table-wrap"):
        table_id = table_wrap.get('id')

        caption_element = table_wrap.find(".//caption")
        caption = ''.join(caption_element.itertext()).strip() if caption_element is not None else ""

        caption_citations = [] 

        foots = []
        for foot in table_wrap.findall(".//table-wrap-foot//p"):
            foots.append(''.join(foot.itertext()).strip())

        # Estrai solo i tag <thead> e <tbody> per il corpo della tabella
        thead_element = table_wrap.find(".//thead")
        tbody_element = table_wrap.find(".//tbody")
        body = ""
        if thead_element is not None and tbody_element is not None:
            thead_html = ET.tostring(thead_element, encoding='unicode', method='xml')
            tbody_html = ET.tostring(tbody_element, encoding='unicode', method='xml')
            body = thead_html + tbody_html

        tbody_element = table_wrap.find(".//tbody")
        if tbody_element is not None:
            cells = extract_cell_content_and_paragraphs(root, tbody_element)

        paragraphs = extract_paragraphs_and_citations(root, table_id , 'table')

        tables.append({
            "table_id": table_id,
            "body": body,
            "caption": caption,
            "caption_citations": caption_citations,
            "foots": foots,
            "paragraphs": paragraphs,
            "cells": cells
        })

    return tables

def extract_data_from_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    pmcid = root.find(".//article-id[@pub-id-type='pmc']")
    pmcid = pmcid.text if pmcid is not None else "N/A"

    title_element = root.find(".//article-title")
    title = ''.join(title_element.itertext()) if title_element is not None else "N/A"

    abstract_texts = []
    for p in root.findall(".//abstract//p"):
        abstract_texts.append(''.join(p.itertext()).strip())
    abstract = ' '.join(abstract_texts)

    keywords = []
    for kwd in root.findall(".//kwd-group/kwd"):
        keyword_text = ''.join(kwd.itertext()).strip()
        if keyword_text:
            keywords.append(keyword_text)

    tables = extract_tables(root)

    figures = extract_figures(root, pmcid)

    data = {
        "pmcid": pmcid,
        "content": {
            "title": title,
            "abstract": abstract,
            "keywords": keywords,
            "tables": tables,
            "figures": figures
        }
    }

    return data

def save_data_to_json(data, json_file):
    # Scrivi i dati in un file JSON
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def process_files(xml_folder, json_folder, limit):
 
    for i, file in enumerate(os.listdir(xml_folder)):
        if i >= limit:
            break
        if file.endswith(".xml"):

            try:
                xml_file = os.path.join(xml_folder, file)
                json_file = os.path.join(json_folder, os.path.splitext(file)[0] + '.json')

                data = extract_data_from_xml(xml_file)
                save_data_to_json(data, json_file)
                print(f"#{i} File processed: {file}")

            except Exception as e:
                print(f"An error occurred: {str(e)}")

# Percorsi delle cartelle
xml_folder = r'C:\Users\Fero\Desktop\HW4\xml da analizzare'
json_folder = r'C:\Users\Fero\Desktop\HW4\json analizzati'

os.makedirs(json_folder, exist_ok=True)

process_files(xml_folder, json_folder, limit=47573)
