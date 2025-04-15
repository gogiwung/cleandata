import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
from pathlib import Path
import re

# 출력 디렉토리 생성
output_dir = Path('output')
output_dir.mkdir(exist_ok=True)

def clean_text(text):
    """텍스트를 정리하는 함수"""
    # 연속된 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    # 앞뒤 공백 제거
    text = text.strip()
    return text

def extract_text_from_element(element):
    """요소에서 텍스트를 추출하는 함수"""
    if isinstance(element, str):
        return clean_text(element)
    
    if element.name in ['script', 'style']:
        return ''
    
    text = []
    for child in element.children:
        if isinstance(child, str):
            cleaned = clean_text(child)
            if cleaned:
                text.append(cleaned)
        elif child.name:
            if child.name in ['p', 'div', 'br']:
                extracted = extract_text_from_element(child)
                if extracted:
                    text.append(extracted)
            else:
                extracted = extract_text_from_element(child)
                if extracted:
                    text.append(extracted)
    return ' '.join(text)

try:
    # URL에서 HTML 콘텐츠 가져오기
    url = 'https://dart.fss.or.kr/report/viewer.do?rcpNo=20240202000550&dcmNo=9601763&eleId=14&offset=343635&length=388506&dtd=dart3.xsd'
    response = requests.get(url)
    response.encoding = 'utf-8'
    html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')
    body = soup.body

    # 결과를 저장할 파일 열기
    with open(output_dir / 'parsed_document.txt', 'w', encoding='utf-8') as output_file:
        current_text = []
        
        for element in body.children:
            if not element.name:  # NavigableString인 경우
                text = clean_text(element)
                if text:
                    current_text.append(text)
            elif element.name == 'table':
                # 현재까지의 텍스트를 처리하고 쓰기
                if current_text:
                    output_file.write(' '.join(current_text) + '\n\n')
                    current_text = []
                
                # 표 추출
                headers = [clean_text(header.get_text()) for header in element.find_all('th')]
                rows = element.find_all('tr')
                table_data = []
                
                # 헤더가 없는 경우 첫 행을 헤더로 사용
                if not headers and rows:
                    first_row = rows[0]
                    headers = [clean_text(cell.get_text()) for cell in first_row.find_all(['td', 'th'])]
                    rows = rows[1:]
                
                # 최대 열 수 계산
                max_cols = len(headers) if headers else 0
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    max_cols = max(max_cols, len(cells))
                
                # 헤더가 없는 경우 빈 헤더 생성
                if not headers:
                    headers = [f'열_{i+1}' for i in range(max_cols)]
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    cells_text = [clean_text(cell.get_text()) for cell in cells]
                    if cells_text:
                        # 열 수가 부족한 경우 빈 문자열로 채움
                        if len(cells_text) < max_cols:
                            cells_text.extend([''] * (max_cols - len(cells_text)))
                        # 열 수가 많은 경우 잘라냄
                        elif len(cells_text) > max_cols:
                            cells_text = cells_text[:max_cols]
                        table_data.append(cells_text)
                
                if table_data:
                    try:
                        df = pd.DataFrame(table_data, columns=headers)
                        # 간단한 텍스트 형식으로 변환
                        table_text = []
                        # 헤더
                        table_text.append(' | '.join(headers))
                        # 구분선
                        table_text.append(' | '.join(['---'] * len(headers)))
                        # 데이터 행
                        for row in table_data:
                            table_text.append(' | '.join(row))
                        # 테이블 텍스트를 하나의 문자열로 결합
                        output_file.write('\n'.join(table_text) + '\n\n')
                    except Exception as e:
                        print(f"테이블 처리 중 에러 발생: {str(e)}")
                        continue
            else:
                text = extract_text_from_element(element)
                if text:
                    current_text.append(text)
        
        # 마지막 텍스트 처리
        if current_text:
            output_file.write(' '.join(current_text) + '\n')

    print("처리가 완료되었습니다. 결과는 'output/parsed_document.txt' 파일에서 확인하실 수 있습니다.")

except Exception as e:
    print(f"에러가 발생했습니다: {str(e)}")
