import pandas as pd
from bs4 import BeautifulSoup
import os
import shutil
from datetime import datetime
import webbrowser
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
    simple_html = "<table border='1'>\n"
    for row in table.find_all('tr'):
        simple_html += "  <tr>\n"
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

            simple_html += f"    <{tag}{attrs}>{text}</{tag}>\n"
        simple_html += "  </tr>\n"
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

def save_files(html_content, rag_text, filename_prefix):
    html_filename = f"output2/{filename_prefix}_original.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    rag_filename = f"output2/{filename_prefix}_rag.txt"
    with open(rag_filename, 'w', encoding='utf-8') as f:
        for elem_type, content in rag_text:
            if elem_type == 'table':
                f.write(f"\n[테이블 (Simple HTML)]\n{content['simple_html']}\n")
            elif elem_type == 'text':
                f.write(f"{content}\n\n")

def compress_html(html):
    # 줄바꿈 및 연속된 공백 제거
    compressed = re.sub(r'\s+', ' ', html).strip()
    return compressed

def count_tokens(text, encoding_name='cl100k_base'):
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def main():
    cleanup_output()
    df = pd.read_parquet("./kms/kms.parquet_20241102.snappy")

    total_tokens = 0
    for idx in range(len(df)):
        print(f"처리 중: 문서 {idx+1}")
        html_content = df['CONT'].iloc[idx]

        rag_text = html_to_rag_text(html_content)

        for elem_type, content in rag_text:
            if elem_type == 'table':
                total_tokens += count_tokens(content['simple_html'])
            elif elem_type == 'text':
                total_tokens += count_tokens(content)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_prefix = f"document_{idx+1}_{timestamp}"
        save_files(html_content, rag_text, filename_prefix)

        print(f"HTML 파일 저장됨: {filename_prefix}_original.html")
        print(f"RAG 텍스트 파일 저장됨: {filename_prefix}_rag.txt")

        print(f"\n전체 문서의 총 토큰 수: {total_tokens}")

        # webbrowser.open(f'file://{os.path.abspath(f"output2/{filename_prefix}_original.html")}')

if __name__ == "__main__":
    main()
