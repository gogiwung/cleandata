import pandas as pd
from bs4 import BeautifulSoup
import os
import shutil
from datetime import datetime
import webbrowser
import re

def cleanup_output():
    """output 디렉토리 초기화"""
    if os.path.exists("output"):
        shutil.rmtree("output")
    os.makedirs("output")

def get_text_content(element):
    """요소의 텍스트 내용 추출"""
    if element.name in ['script', 'style']:
        return None
    
    # 텍스트 노드인 경우
    if element.string:
        text = element.string.strip()
        return text if text else None
    
    # 자식 요소가 있는 경우
    texts = []
    for child in element.children:
        if child.name:
            child_text = get_text_content(child)
            if child_text:
                texts.append(child_text)
        elif child.string and child.string.strip():
            texts.append(child.string.strip())
    
    return ' '.join(texts) if texts else None

def process_table(table):
    """테이블을 마크다운 형식으로 변환"""
    markdown_rows = []
    max_cols = 0
    
    # 테이블 구조 분석
    for row in table.find_all('tr'):
        md_row = []
        col_index = 0
        
        for cell in row.find_all(['td', 'th']):
            # 셀 내용 정리
            text = ' '.join(cell.stripped_strings)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 병합 정보 추출
            rowspan = int(cell.get('rowspan', 1))
            colspan = int(cell.get('colspan', 1))
            
            # 병합 정보를 영어로 표시
            notes = []
            if rowspan > 1:
                notes.append(f"rowspan: {rowspan} row{'s' if rowspan != 1 else ''}")
            if colspan > 1:
                notes.append(f"colspan: {colspan} column{'s' if colspan != 1 else ''}")
            
            # 병합 정보 추가
            if notes:
                text += f" [merge: {', '.join(notes)}]"
            
            md_row.append(text)
            col_index += colspan
        
        if md_row:
            max_cols = max(max_cols, col_index)
            markdown_rows.append("| " + " | ".join(md_row) + " |")
    
    # 헤더 구분선 추가
    if len(markdown_rows) >= 2:
        divider = "| " + " | ".join(['---'] * max_cols) + " |"
        markdown_rows.insert(1, divider)
    
    # 테이블 구조 정보 추가
    markdown_rows.insert(0, f"[Table Structure: {max_cols} columns]")
    
    return "\n".join(markdown_rows)

def html_to_rag_text(html_content):
    """HTML을 RAG에 적합한 텍스트로 변환"""
    soup = BeautifulSoup(html_content, 'html.parser')
    elements = []
    
    # 제목 추출
    title = soup.find(['h1', 'h2', 'h3'])
    if title:
        elements.append(('title', get_text_content(title)))
    
    # 본문 내용 추출
    for element in soup.find_all(['p', 'div', 'table']):
        if element.name == 'table':
            elements.append(('table', process_table(element)))
        else:
            text = get_text_content(element)
            if text:
                elements.append(('text', text))
    
    return elements

def save_files(html_content, rag_text, filename_prefix):
    """HTML과 RAG 텍스트를 파일로 저장"""
    # HTML 파일 저장
    html_filename = f"output/{filename_prefix}_original.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # RAG 텍스트 파일 저장
    rag_filename = f"output/{filename_prefix}_rag.txt"
    with open(rag_filename, 'w', encoding='utf-8') as f:
        for elem_type, content in rag_text:
            if elem_type == 'title':
                f.write(f"\n{'=' * 50}\n")
                f.write(f"{content}\n")
                f.write(f"{'=' * 50}\n\n")
            elif elem_type == 'table':
                f.write(f"\n[테이블]\n{content}\n")
            elif elem_type == 'text':
                f.write(f"{content}\n\n")

def main():
    # 출력 디렉토리 초기화
    cleanup_output()
    
    # Parquet 파일 읽기
    df = pd.read_parquet("./kms/kms.parquet_20241102.snappy")
    
    # 각 문서 처리
    for idx in range(len(df)):
        print(f"\n처리 중: 문서 {idx+1}")
        html_content = df['CONT'].iloc[idx]
        
        # RAG 텍스트로 변환
        rag_text = html_to_rag_text(html_content)
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_prefix = f"document_{idx+1}_{timestamp}"
        save_files(html_content, rag_text, filename_prefix)
        
        print(f"HTML 파일 저장됨: {filename_prefix}_original.html")
        print(f"RAG 텍스트 파일 저장됨: {filename_prefix}_rag.txt")
        
        # HTML 파일 브라우저로 열기
        webbrowser.open(f'file://{os.path.abspath(f"output/{filename_prefix}_original.html")}')

if __name__ == "__main__":
    main()