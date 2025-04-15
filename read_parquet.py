import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path

def read_and_display_parquet(file_path):
    try:
        # 파일이 존재하는지 확인
        if not file_path.exists():
            print(f"파일을 찾을 수 없습니다: {file_path}")
            return
        
        # Parquet 파일을 DataFrame으로 읽기
        print("\n파일 읽는 중...")
        df = pd.read_parquet(file_path)
        
        # 기본 정보 출력
        print("\n=== 데이터프레임 정보 ===")
        print(f"행 수: {len(df)}")
        print(f"열 수: {len(df.columns)}")
        print("\n열 이름:")
        for col in df.columns:
            print(f"- {col}")
        
        # 데이터 샘플 출력
        print("\n=== 데이터 샘플 (처음 5행) ===")
        print(df.head())
        
        # 각 열의 데이터 타입 출력
        print("\n=== 데이터 타입 ===")
        print(df.dtypes)
        
        # 기본 통계 정보 출력
        print("\n=== 기본 통계 정보 ===")
        print(df.describe())
        
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    # 파일 경로 지정
    file_path = Path("C:/Users/shic/Desktop/test/kms/kms.parquet_20241104.snappy")
    read_and_display_parquet(file_path) 