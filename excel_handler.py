"""
엑셀 파일 처리 모듈
엑셀 파일 로드 및 시트 선택 기능 제공
"""

import pandas as pd
import os


class ExcelHandler:
    """엑셀 파일 처리 클래스"""
    
    def __init__(self):
        self.file_path = None
        self.current_sheet = None
        self.sheet_names = []
    
    def load_file(self, file_path):
        """
        엑셀 파일 로드
        
        Args:
            file_path: 엑셀 파일 경로
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        self.file_path = file_path
        
        # 엑셀 파일의 모든 시트 이름 가져오기
        try:
            excel_file = pd.ExcelFile(file_path)
            self.sheet_names = excel_file.sheet_names
        except Exception as e:
            raise Exception(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {str(e)}")
    
    def get_sheet_names(self):
        """사용 가능한 시트 이름 목록 반환"""
        return self.sheet_names.copy()
    
    def load_sheet(self, sheet_name):
        """
        지정된 시트를 로드
        
        Args:
            sheet_name: 시트 이름
            
        Returns:
            pandas DataFrame: 시트 데이터
        """
        if not self.file_path:
            raise Exception("먼저 엑셀 파일을 로드해주세요.")
        
        if sheet_name not in self.sheet_names:
            raise ValueError(f"시트를 찾을 수 없습니다: {sheet_name}")
        
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            self.current_sheet = sheet_name
            return df
        except Exception as e:
            raise Exception(f"시트를 로드하는 중 오류가 발생했습니다: {str(e)}")
    
    def file_loaded(self):
        """파일이 로드되었는지 확인"""
        return self.file_path is not None and len(self.sheet_names) > 0
