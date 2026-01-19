"""
파트넘버 데이터베이스 모듈
SQLite를 사용하여 파트넘버 정보를 캐싱
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, Optional


class PartDatabase:
    """파트넘버 데이터베이스 클래스"""
    
    def __init__(self, db_path: str = "parts_cache.db"):
        """
        초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.connection = None
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            # 파트넘버 정보 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parts (
                    part_number TEXT PRIMARY KEY,
                    manufacturer TEXT NOT NULL,
                    mounting_type TEXT NOT NULL,
                    description TEXT,
                    product_url TEXT,
                    datasheet_url TEXT,
                    quantity_available INTEGER,
                    unit_price REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 인덱스 생성 (검색 성능 향상)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_manufacturer 
                ON parts(manufacturer)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mounting_type 
                ON parts(mounting_type)
            """)
            
            # API 호출 통계 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_date DATE NOT NULL,
                    call_count INTEGER DEFAULT 0,
                    UNIQUE(call_date)
                )
            """)
            
            self.connection.commit()
            
        except sqlite3.Error as e:
            print(f"데이터베이스 초기화 오류: {str(e)}")
            raise
    
    def get_part(self, part_number: str) -> Optional[Dict]:
        """
        데이터베이스에서 파트넘버 정보 조회
        
        Args:
            part_number: 파트넘버
            
        Returns:
            dict: 파트 정보 또는 None
        """
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT part_number, manufacturer, mounting_type, description,
                       product_url, datasheet_url, quantity_available, unit_price,
                       created_at, updated_at
                FROM parts
                WHERE part_number = ?
            """, (part_number.strip(),))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'PartNumber': row[0],
                    'Manufacturer': row[1],
                    'MountingType': row[2],
                    'Description': row[3] or 'N/A',
                    'ProductUrl': row[4] or '',
                    'DatasheetUrl': row[5] or '',
                    'QuantityAvailable': row[6] or 0,
                    'UnitPrice': row[7] or 0,
                    'CreatedAt': row[8],
                    'UpdatedAt': row[9],
                    'Source': 'Database'  # DB에서 조회된 것임을 표시
                }
            
            return None
            
        except sqlite3.Error as e:
            print(f"데이터베이스 조회 오류 ({part_number}): {str(e)}")
            return None
    
    def save_part(self, part_data: Dict) -> bool:
        """
        파트넘버 정보를 데이터베이스에 저장
        
        Args:
            part_data: 파트 정보 딕셔너리
            
        Returns:
            bool: 저장 성공 여부
        """
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # 현재 시간
            now = datetime.now().isoformat()
            
            # UPSERT (INSERT OR REPLACE)
            cursor.execute("""
                INSERT OR REPLACE INTO parts (
                    part_number, manufacturer, mounting_type, description,
                    product_url, datasheet_url, quantity_available, unit_price,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 
                    COALESCE((SELECT created_at FROM parts WHERE part_number = ?), ?),
                    ?
                )
            """, (
                part_data.get('PartNumber', '').strip(),
                part_data.get('Manufacturer', 'N/A'),
                part_data.get('MountingType', 'N/A'),
                part_data.get('Description', 'N/A'),
                part_data.get('ProductUrl', ''),
                part_data.get('DatasheetUrl', ''),
                part_data.get('QuantityAvailable', 0),
                part_data.get('UnitPrice', 0),
                part_data.get('PartNumber', '').strip(),  # created_at 유지용
                now,  # 새로 생성 시 created_at
                now   # updated_at
            ))
            
            self.connection.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"데이터베이스 저장 오류: {str(e)}")
            return False
    
    def get_all_parts(self) -> list:
        """
        데이터베이스의 모든 파트넘버 조회
        
        Returns:
            list: 파트넘버 리스트
        """
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT part_number FROM parts ORDER BY part_number")
            return [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"데이터베이스 조회 오류: {str(e)}")
            return []
    
    def increment_api_call(self) -> bool:
        """
        오늘 날짜의 API 호출 횟수 증가
        
        Returns:
            bool: 성공 여부
        """
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            today = datetime.now().date().isoformat()
            
            # 오늘 날짜의 레코드가 있으면 증가, 없으면 생성
            cursor.execute("""
                INSERT INTO api_calls (call_date, call_count)
                VALUES (?, 1)
                ON CONFLICT(call_date) DO UPDATE SET
                    call_count = call_count + 1
            """, (today,))
            
            self.connection.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"API 호출 카운트 증가 오류: {str(e)}")
            return False
    
    def get_today_api_calls(self) -> int:
        """
        오늘 날짜의 API 호출 횟수 조회
        
        Returns:
            int: 오늘의 API 호출 횟수
        """
        if not self.connection:
            return 0
        
        try:
            cursor = self.connection.cursor()
            today = datetime.now().date().isoformat()
            
            cursor.execute("""
                SELECT call_count FROM api_calls
                WHERE call_date = ?
            """, (today,))
            
            row = cursor.fetchone()
            return row[0] if row else 0
            
        except sqlite3.Error as e:
            print(f"API 호출 횟수 조회 오류: {str(e)}")
            return 0
    
    def get_api_call_stats(self, limit: int = 30) -> list:
        """
        최근 API 호출 통계 조회
        
        Args:
            limit: 조회할 일수
            
        Returns:
            list: API 호출 통계 리스트
        """
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT call_date, call_count
                FROM api_calls
                ORDER BY call_date DESC
                LIMIT ?
            """, (limit,))
            
            return [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"API 통계 조회 오류: {str(e)}")
            return []
    
    def get_stats(self) -> Dict:
        """
        데이터베이스 통계 정보 조회
        
        Returns:
            dict: 통계 정보
        """
        if not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            
            # 전체 파트 수
            cursor.execute("SELECT COUNT(*) FROM parts")
            total_parts = cursor.fetchone()[0]
            
            # 제조사 수
            cursor.execute("SELECT COUNT(DISTINCT manufacturer) FROM parts")
            total_manufacturers = cursor.fetchone()[0]
            
            # 마운팅 타입 수
            cursor.execute("SELECT COUNT(DISTINCT mounting_type) FROM parts WHERE mounting_type != 'N/A'")
            total_mounting_types = cursor.fetchone()[0]
            
            # 오늘 API 호출 횟수
            today_calls = self.get_today_api_calls()
            
            return {
                'total_parts': total_parts,
                'total_manufacturers': total_manufacturers,
                'total_mounting_types': total_mounting_types,
                'today_api_calls': today_calls
            }
            
        except sqlite3.Error as e:
            print(f"통계 정보 조회 오류: {str(e)}")
            return {}
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __del__(self):
        """소멸자: 데이터베이스 연결 종료"""
        self.close()
