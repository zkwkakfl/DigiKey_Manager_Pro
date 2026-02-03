"""
디지키 API 클라이언트 모듈
디지키 API를 사용하여 파트넘버 정보 조회
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional


class RateLimitExceeded(Exception):
    """API 호출 한도 초과 예외"""
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class DigikeyAPIClient:
    """디지키 API 클라이언트 클래스"""
    
    # 디지키 API 엔드포인트 (샌드박스 환경)
    SANDBOX_BASE_URL = "https://sandbox-api.digikey.com"
    PRODUCTION_BASE_URL = "https://api.digikey.com"
    
    def __init__(self, client_id: str = None, client_secret: str = None, use_sandbox: bool = False):
        """
        초기화
        
        Args:
            client_id: 디지키 API Client ID
            client_secret: 디지키 API Client Secret
            use_sandbox: 샌드박스 환경 사용 여부 (기본값: True)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.use_sandbox = use_sandbox
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.token_file = "token.json"  # 토큰 저장 파일
        
        # API 기본 URL 설정
        self.base_url = self.SANDBOX_BASE_URL if use_sandbox else self.PRODUCTION_BASE_URL
        
        # token.json 파일에서 토큰 로드 시도
        self.load_token_from_file()
    
    def set_credentials(self, client_id: str, client_secret: str):
        """
        API 인증 정보 설정
        
        Args:
            client_id: 디지키 API Client ID
            client_secret: 디지키 API Client Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None  # 새 인증 정보로 토큰 무효화
    
    def is_configured(self) -> bool:
        """API 설정이 완료되었는지 확인"""
        return self.client_id is not None and self.client_secret is not None
    
    def load_token_from_file(self):
        """token.json 파일에서 토큰 로드"""
        if os.path.exists(self.token_file):
            try:
                # UTF-8 BOM 처리 (utf-8-sig 사용)
                with open(self.token_file, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                
                # 빈 파일이거나 빈 내용인 경우 처리
                if not content or not content.strip():
                    return
                
                # JSON 형식 정리: 첫 번째 '{'부터 마지막 '}'까지 추출
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                
                if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                    print("token.json 파일에 유효한 JSON 객체를 찾을 수 없습니다.")
                    return
                
                json_content = content[start_idx:end_idx + 1]
                token_data = json.loads(json_content)
                
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                
                # 만료 시간 계산
                expires_in = token_data.get("expires_in", 0)
                if expires_in > 0:
                    self.token_expires_at = time.time() + expires_in - 100
                    
            except json.JSONDecodeError as e:
                print(f"token.json 파일 JSON 파싱 오류: {str(e)}")
            except Exception as e:
                print(f"token.json 파일 읽기 오류: {str(e)}")
    
    def save_token_to_file(self, token_data: dict):
        """토큰을 token.json 파일에 저장"""
        try:
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, indent=4)
        except Exception as e:
            print(f"token.json 파일 저장 오류: {str(e)}")
    
    def refresh_access_token(self) -> str:
        """refresh_token을 사용하여 새 액세스 토큰 획득"""
        if not self.refresh_token:
            raise Exception("refresh_token이 없습니다.")
        
        if not self.is_configured():
            raise Exception("API 인증 정보가 설정되지 않았습니다.")
        
        token_url = f"{self.base_url}/v1/oauth2/token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data, timeout=15)
            
            if response.status_code == 401:
                raise Exception("refresh_token이 만료되었거나 유효하지 않습니다. 새로 인증이 필요합니다.")
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token", self.refresh_token)  # 새 refresh_token이 있으면 업데이트
            
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in - 100
            
            # 토큰 저장
            self.save_token_to_file(token_data)
            
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"토큰 갱신 중 오류가 발생했습니다: {str(e)}")
    
    def get_access_token(self) -> str:
        """
        OAuth 2.0 액세스 토큰 획득
        
        Returns:
            str: 액세스 토큰
        """
        if not self.is_configured():
            raise Exception("API 인증 정보가 설정되지 않았습니다.")
        
        # 토큰이 아직 유효한 경우 재사용
        if self.access_token and self.token_expires_at:
            if time.time() < self.token_expires_at:
                return self.access_token
        
        # refresh_token이 있으면 갱신 시도
        if self.refresh_token:
            try:
                return self.refresh_access_token()
            except Exception as e:
                print(f"토큰 갱신 실패, 새 토큰 요청: {str(e)}")
                # refresh_token이 실패하면 새로 발급 시도
        
        # 새 토큰 요청 (client_credentials 방식)
        token_url = f"{self.base_url}/v1/oauth2/token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data, timeout=15)
            
            # 응답 상태 코드 확인
            if response.status_code == 401:
                error_detail = ""
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error_description", error_json.get("error", ""))
                except:
                    error_detail = response.text[:200] if response.text else ""
                
                raise Exception(
                    f"토큰 획득 실패 (401 Unauthorized):\n"
                    f"• API 키가 올바른지 확인하세요\n"
                    f"• 샌드박스 키는 샌드박스 API, 프로덕션 키는 프로덕션 API를 사용해야 합니다\n"
                    f"• Developer Portal에서 API Product 구독 상태를 확인하세요\n"
                    f"• 현재 환경: {'샌드박스' if self.use_sandbox else '프로덕션'}\n"
                    f"• 상세 오류: {error_detail}"
                )
            
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            if not self.access_token:
                raise Exception("토큰 응답에 access_token이 없습니다.")
            
            # 토큰 만료 시간 저장 (기본적으로 3600초 유효, 여유있게 3500초로 설정)
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in - 100
            
            # refresh_token이 있으면 저장
            if "refresh_token" in token_data:
                self.refresh_token = token_data.get("refresh_token")
            
            # 토큰 저장
            self.save_token_to_file(token_data)
            
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    # 이미 위에서 처리했지만, 혹시 모를 경우를 위해
                    raise Exception(f"토큰 획득 중 인증 오류가 발생했습니다 (401): API 키와 환경 설정을 확인하세요.")
            raise Exception(f"토큰 획득 중 오류가 발생했습니다: {str(e)}")
    
    def _product_to_result(self, product: dict, part_number: str) -> Dict:
        """API 응답의 product 딕셔너리를 공통 결과 형식으로 변환"""
        if isinstance(product, list) and len(product) > 0:
            product = product[0]
        if not isinstance(product, dict):
            return {
                "PartNumber": part_number,
                "Manufacturer": "N/A",
                "MountingType": "N/A",
                "Description": "N/A",
                "ProductUrl": "",
                "DatasheetUrl": "",
                "QuantityAvailable": 0,
                "UnitPrice": 0
            }
        manufacturer = "N/A"
        if "Manufacturer" in product:
            if isinstance(product["Manufacturer"], dict):
                manufacturer = product["Manufacturer"].get("Name") or product["Manufacturer"].get("Value", "N/A")
            elif isinstance(product["Manufacturer"], str):
                manufacturer = product["Manufacturer"]
        description = "N/A"
        if "DetailedDescription" in product:
            desc_value = product.get("DetailedDescription")
            if isinstance(desc_value, dict):
                description = desc_value.get("DetailedDescription") or desc_value.get("ProductDescription") or "N/A"
            elif isinstance(desc_value, str):
                description = desc_value
        elif "Description" in product:
            desc_value = product.get("Description")
            if isinstance(desc_value, dict):
                description = desc_value.get("DetailedDescription") or desc_value.get("ProductDescription") or "N/A"
            elif isinstance(desc_value, str):
                description = desc_value
        result = {
            "PartNumber": product.get("DigiKeyPartNumber") or product.get("PartNumber") or part_number,
            "Manufacturer": manufacturer,
            "MountingType": "N/A",
            "Description": description,
            "ProductUrl": product.get("ProductUrl") or product.get("Url") or "",
            "DatasheetUrl": product.get("PrimaryDatasheet") or product.get("DatasheetUrl") or "",
            "QuantityAvailable": product.get("QuantityAvailable", 0),
            "UnitPrice": 0
        }
        if "StandardPricing" in product and product["StandardPricing"]:
            if isinstance(product["StandardPricing"], list) and len(product["StandardPricing"]) > 0:
                result["UnitPrice"] = product["StandardPricing"][0].get("UnitPrice", 0)
        params = product.get("Parameters", [])
        if isinstance(params, list):
            for param in params:
                if isinstance(param, dict):
                    param_text = param.get("ParameterText") or param.get("Parameter") or param.get("Name", "")
                    if param_text == "Mounting Type":
                        result["MountingType"] = param.get("ValueText") or param.get("Value", "N/A")
                        break
        elif isinstance(params, dict):
            result["MountingType"] = params.get("MountingType") or params.get("Mounting Type", "N/A")
        return result
    
    def search_part(self, part_number: str) -> Optional[Dict]:
        """
        파트넘버로 제품 정보 검색
        
        Args:
            part_number: 파트넘버
            
        Returns:
            dict: 제품 정보 (Manufacturer, MountingType 등 포함)
        """
        if not self.is_configured():
            return None
        
        try:
            # 액세스 토큰 획득
            token = self.get_access_token()
            
            # 제품 검색 API 호출 (올바른 엔드포인트)
            search_url = f"{self.base_url}/products/v4/search/keyword"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-DIGIKEY-Client-Id": self.client_id,
                "X-DIGIKEY-Locale-Site": "US",
                "X-DIGIKEY-Locale-Language": "en",
                "X-DIGIKEY-Locale-Currency": "USD"
            }
            
            # 검색 요청 데이터
            payload = {
                "Keywords": part_number,
                "RecordCount": 1,
                "RecordStartPosition": 0
            }
            
            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
            
            # 401 오류 발생 시 토큰 갱신 후 재시도
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    if "expired" in error_data.get("detail", "").lower() or "Bearer token is expired" in error_data.get("detail", ""):
                        # 토큰 만료 시 refresh_token으로 갱신 시도
                        if self.refresh_token:
                            print(f"토큰 만료 감지, refresh_token으로 갱신 시도...")
                            self.refresh_access_token()
                            # 새 토큰으로 재시도
                            token = self.get_access_token()
                            headers["Authorization"] = f"Bearer {token}"
                            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
                        else:
                            # refresh_token이 없으면 새 토큰 요청
                            print(f"refresh_token 없음, 새 토큰 요청...")
                            self.access_token = None
                            self.token_expires_at = None
                            token = self.get_access_token()
                            headers["Authorization"] = f"Bearer {token}"
                            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
                except Exception as refresh_error:
                    print(f"토큰 갱신 실패: {str(refresh_error)}")
                    # 갱신 실패 시 원래 오류 메시지 반환
                    error_msg = f"API 호출 실패 (상태 코드: 401 - 토큰 만료)"
                    try:
                        error_data = response.json()
                        error_msg += f"\n오류: {error_data.get('detail', error_data)}"
                    except:
                        error_msg += f"\n응답: {response.text[:200]}"
                    raise Exception(error_msg)
            
            # 응답 상태 확인
            if response.status_code != 200:
                error_msg = f"API 호출 실패 (상태 코드: {response.status_code})"
                
                # 429 오류 (일일 호출 제한 초과) 특별 처리
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '알 수 없음')
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', '')
                        error_msg = f"API 일일 호출 제한 초과 (429 Too Many Requests)\n"
                        error_msg += f"상세: {detail}\n"
                        error_msg += f"재시도 가능 시간: {retry_after}초 후"
                    except:
                        error_msg += f"\n응답: {response.text[:200]}"
                        error_msg += f"\n재시도 가능 시간: {retry_after}초 후"
                    
                    # RateLimitExceeded 예외 발생 (조회 중단을 위해)
                    try:
                        retry_after_int = int(retry_after) if retry_after != '알 수 없음' else None
                    except:
                        retry_after_int = None
                    raise RateLimitExceeded(error_msg, retry_after_int)
                else:
                    try:
                        error_data = response.json()
                        error_msg += f"\n오류: {error_data}"
                    except:
                        error_msg += f"\n응답: {response.text[:200]}"
                
                raise Exception(error_msg)
            
            response.raise_for_status()
            data = response.json()
            
            # 디버깅: 응답 구조 확인
            # print(f"API 응답 구조: {list(data.keys())}")  # 필요시 주석 해제
            
            # 검색 결과가 있는 경우 (다양한 응답 구조 대응)
            search_results = None
            if "SearchResults" in data:
                search_results = data["SearchResults"]
            elif "Products" in data:
                search_results = data["Products"]
            elif isinstance(data, list):
                search_results = data
            
            if search_results and len(search_results) > 0:
                return self._product_to_result(search_results[0], part_number)
            else:
                # 검색 결과가 없는 경우
                return {
                    "PartNumber": part_number,
                    "Manufacturer": "검색 결과 없음",
                    "MountingType": "N/A",
                    "Description": "파트넘버를 찾을 수 없습니다."
                }
                
        except requests.exceptions.RequestException as e:
            # API 오류 발생 시
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = f"{error_msg}\n상세: {error_data}"
                except:
                    error_msg = f"{error_msg}\n응답: {e.response.text[:200]}"
            
            print(f"파트넘버 조회 오류 ({part_number}): {error_msg}")
            return {
                "PartNumber": part_number,
                "Manufacturer": "API 오류",
                "MountingType": "N/A",
                "Error": error_msg
            }
        except Exception as e:
            # 기타 오류
            print(f"파트넘버 조회 오류 ({part_number}): {str(e)}")
            return {
                "PartNumber": part_number,
                "Manufacturer": "오류 발생",
                "MountingType": "N/A",
                "Error": str(e)
            }
    
    def search_part_multiple(self, part_number: str, record_count: int = 15) -> List[Dict]:
        """
        키워드로 여러 개의 유사 제품 검색 (1회 API 호출)
        
        Args:
            part_number: 검색 키워드(파트넘버)
            record_count: 반환받을 최대 건수 (기본 15)
            
        Returns:
            list: 제품 정보 딕셔너리 목록 (0개 이상). 오류 시 빈 목록.
        """
        if not self.is_configured():
            return []
        try:
            token = self.get_access_token()
            search_url = f"{self.base_url}/products/v4/search/keyword"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-DIGIKEY-Client-Id": self.client_id,
                "X-DIGIKEY-Locale-Site": "US",
                "X-DIGIKEY-Locale-Language": "en",
                "X-DIGIKEY-Locale-Currency": "USD"
            }
            payload = {
                "Keywords": part_number,
                "RecordCount": min(record_count, 50),
                "RecordStartPosition": 0
            }
            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    if "expired" in error_data.get("detail", "").lower() or "Bearer token is expired" in error_data.get("detail", ""):
                        if self.refresh_token:
                            self.refresh_access_token()
                            token = self.get_access_token()
                            headers["Authorization"] = f"Bearer {token}"
                            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
                        else:
                            self.access_token = None
                            self.token_expires_at = None
                            token = self.get_access_token()
                            headers["Authorization"] = f"Bearer {token}"
                            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
                except Exception:
                    return []
            if response.status_code == 429:
                try:
                    retry_after = response.headers.get("Retry-After", "알 수 없음")
                    retry_after_int = int(retry_after) if retry_after != "알 수 없음" else None
                except Exception:
                    retry_after_int = None
                raise RateLimitExceeded("API 일일 호출 제한 초과", retry_after_int)
            if response.status_code != 200:
                return []
            data = response.json()
            search_results = None
            if "SearchResults" in data:
                search_results = data["SearchResults"]
            elif "Products" in data:
                search_results = data["Products"]
            elif isinstance(data, list):
                search_results = data
            if not search_results or len(search_results) == 0:
                return []
            results = []
            for product in search_results:
                try:
                    r = self._product_to_result(product, part_number)
                    if r.get("Manufacturer") != "검색 결과 없음":
                        results.append(r)
                except Exception:
                    continue
            return results
        except RateLimitExceeded:
            raise
        except Exception as e:
            print(f"유사 제품 검색 오류 ({part_number}): {str(e)}")
            return []
    
    def get_product_details(self, part_number: str) -> Optional[Dict]:
        """
        파트넘버로 제품 상세 정보 조회 (별도 엔드포인트 사용 시)
        
        Args:
            part_number: 파트넘버
            
        Returns:
            dict: 제품 상세 정보
        """
        # search_part와 동일하게 구현 (필요시 별도 엔드포인트로 확장 가능)
        return self.search_part(part_number)
