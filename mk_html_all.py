import pandas as pd
from bs4 import BeautifulSoup
import os
import shutil
from datetime import datetime
import re
import tiktoken

def cleanup_output():
    if os.path.exists("output2"):
        shutil.rmtree("output2")
    os.makedirs("output2")

def get_text_content(element):
    if element.name in ['script', 'style']:
        return None

    if element.string:
        text = element.string.strip()
        return text if text else None

    texts = []
    for child in element.children:
        if child.name:
            child_text = get_text_content(child)
            if child_text:
                texts.append(child_text)
        elif child.string and child.string.strip():
            texts.append(child.string.strip())

    return ' '.join(texts) if texts else None

def table_to_simple_html(table):
    simple_html = "<table border='1'>"
    for row in table.find_all('tr'):
        simple_html += "<tr>"
        for cell in row.find_all(['td', 'th']):
            tag = cell.name
            text = ' '.join(cell.stripped_strings)
            text = re.sub(r'\s+', ' ', text).strip()

            rowspan = cell.get('rowspan')
            colspan = cell.get('colspan')

            attrs = ''
            if rowspan:
                attrs += f" rowspan='{rowspan}'"
            if colspan:
                attrs += f" colspan='{colspan}'"

            simple_html += f"<{tag}{attrs}>{text}</{tag}>"
        simple_html += "</tr>"
    simple_html += "</table>"

    return compress_html(simple_html)

def html_to_rag_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = []

    body = soup.body or soup

    for element in body.descendants:
        if not hasattr(element, 'name'):
            continue

        if element.name not in ['p', 'div', 'table']:
            continue

        if any(parent.name == 'table' for parent in element.parents if parent != element):
            continue

        if element.name == 'table':
            simple_html = table_to_simple_html(element)
            elements.append(('table', {'simple_html': simple_html}))
        else:
            text = get_text_content(element)
            if text:
                elements.append(('text', text))

    return elements

def save_merged_text(all_text_blocks):
    output_path = "output2/merged_rag_text.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        for block in all_text_blocks:
            f.write(block + "\n\n")
    print(f"병합된 텍스트 파일 저장됨: {output_path}")

def compress_html(html):
    compressed = re.sub(r'\s+', ' ', html).strip()
    return compressed

def count_tokens(text, encoding_name='cl100k_base'):
    if text is None:
        return 0
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

def main():
    cleanup_output()
    total_tokens = 0
    all_text_blocks = []

    folder_path = "./kms"  # Snappy 파일들이 있는 폴더 경로
    for filename in os.listdir(folder_path):
        if not filename.endswith(".snappy"):
            continue

        filepath = os.path.join(folder_path, filename)
        df = pd.read_parquet(filepath)

        for idx in range(len(df)):
            html_content = df['CONT'].iloc[idx]
            if html_content is None:
                continue

            rag_text = html_to_rag_text(html_content)

            for elem_type, content in rag_text:
                if elem_type == 'table':
                    block = content['simple_html']
                elif elem_type == 'text':
                    block = content
                else:
                    continue

                if block:
                    total_tokens += count_tokens(block)
                    all_text_blocks.append(block)

        print(f"처리 완료: {filename}")

    save_merged_text(all_text_blocks)
    print(f"\n전체 문서의 총 토큰 수: {total_tokens}")

if __name__ == "__main__":
    main()
