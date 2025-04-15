from bs4 import BeautifulSoup
import re

def html_to_markdown(html_content):
    """
    HTML 내용을 마크다운 형식으로 변환합니다.
    
    Args:
        html_content (str): 변환할 HTML 내용
        
    Returns:
        str: 마크다운 형식으로 변환된 텍스트
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 테이블 처리
    for table in soup.find_all('table'):
        markdown_table = convert_table_to_markdown(table)
        table.replace_with(markdown_table)
    
    # 기타 HTML 태그 처리
    text = soup.get_text(separator='\n', strip=True)
    
    # 연속된 빈 줄 제거
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def convert_table_to_markdown(table):
    """
    HTML 테이블을 마크다운 테이블로 변환합니다.
    
    Args:
        table (bs4.element.Tag): BeautifulSoup 테이블 태그
        
    Returns:
        str: 마크다운 형식의 테이블
    """
    rows = table.find_all('tr')
    if not rows:
        return ""
    
    # 헤더 처리
    headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
    markdown = "| " + " | ".join(headers) + " |\n"
    markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    # 데이터 행 처리
    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all('td')]
        markdown += "| " + " | ".join(cells) + " |\n"
    
    return markdown

def main():
    # 예제 사용
    html_example = """
    <html>
        <body>
            <h1>제목</h1>
            <p>일반 텍스트</p>
            <table>
                <tr>
                    <th>이름</th>
                    <th>나이</th>
                </tr>
                <tr>
                    <td>홍길동</td>
                    <td>30</td>
                </tr>
                <tr>
                    <td>김철수</td>
                    <td>25</td>
                </tr>
            </table>
        </body>
    </html>
    """
    
    markdown = html_to_markdown(html_example)
    print(markdown)

if __name__ == "__main__":
    main() 