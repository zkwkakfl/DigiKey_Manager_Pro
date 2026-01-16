"""
디지키 API를 사용한 파트넘버 조회 애플리케이션
엑셀 파일에서 시트를 선택하고, 파트넘버를 더블클릭하여 조회하는 GUI 프로그램
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from excel_handler import ExcelHandler
from digikey_api import DigikeyAPIClient


class DigikeyViewerApp:
    """메인 애플리케이션 클래스"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("디지키 파트넘버 조회 프로그램")
        self.root.geometry("1200x700")
        
        # 데이터 저장 변수
        self.excel_handler = ExcelHandler()
        self.digikey_api = DigikeyAPIClient()
        self.current_df = None  # 현재 로드된 엑셀 데이터
        self.query_results = []  # 조회 결과 저장
        self.config_file = "config.txt"  # 설정 파일 경로
        
        # config 파일에서 API 키 로드
        self.load_config()
        
        # 디지키 API 설정 확인
        self.check_api_config()
        
        # GUI 초기화 (먼저 UI를 생성해야 함)
        self.init_ui()
        
        # 시작 시 파일 및 시트 선택 유저폼 표시 (약간의 지연 후)
        self.root.after(100, self.show_initial_setup)
    
    def init_ui(self):
        """UI 초기화"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 윈도우 종료 프로토콜 설정
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 메뉴바
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="엑셀 파일 열기", command=self.load_excel_file)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.on_closing)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="설정", menu=settings_menu)
        settings_menu.add_command(label="디지키 API 설정", command=self.show_api_settings)
        
        # 상단 도구바
        toolbar = ttk.Frame(main_frame)
        toolbar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(toolbar, text="엑셀 파일 열기", command=self.load_excel_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="시트 선택", command=self.select_sheet).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="디지키 API 설정", command=self.show_api_settings).pack(side=tk.LEFT, padx=5)
        
        self.sheet_label = ttk.Label(toolbar, text="선택된 시트: 없음")
        self.sheet_label.pack(side=tk.LEFT, padx=10)
        
        # 탭 위젯 생성
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 탭 1: 시트 데이터 리스트뷰
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="시트 데이터")
        self.setup_tab1()
        
        # 탭 2: 조회 목록 및 상세정보
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="조회 결과")
        self.setup_tab2()
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def setup_tab1(self):
        """탭 1 설정: 시트 데이터 표시"""
        # 프레임 설정
        frame = ttk.Frame(self.tab1, padding="5")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 트리뷰 (리스트뷰 역할) 및 스크롤바
        scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
        
        self.tree1 = ttk.Treeview(frame, yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=self.tree1.yview)
        scrollbar_x.config(command=self.tree1.xview)
        
        # 그리드 배치
        self.tree1.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # 더블클릭 이벤트 바인딩
        self.tree1.bind("<Double-1>", self.on_part_double_click)
    
    def setup_tab2(self):
        """탭 2 설정: 조회 결과 및 상세정보"""
        # 좌우 분할 프레임
        paned = ttk.PanedWindow(self.tab2, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 왼쪽: 조회 결과 리스트뷰
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=3)
        
        scrollbar_y2 = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        scrollbar_x2 = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL)
        
        self.tree2 = ttk.Treeview(left_frame, yscrollcommand=scrollbar_y2.set, xscrollcommand=scrollbar_x2.set)
        scrollbar_y2.config(command=self.tree2.yview)
        scrollbar_x2.config(command=self.tree2.xview)
        
        self.tree2.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y2.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x2.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # 더블클릭 이벤트 바인딩
        self.tree2.bind("<Double-1>", self.on_query_result_double_click)
        
        # 오른쪽: 상세정보 패널
        right_frame = ttk.Frame(paned, padding="10")
        paned.add(right_frame, weight=2)
        
        # 상세정보 라벨
        ttk.Label(right_frame, text="상세 정보", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # 상세정보 텍스트 위젯 (읽기 전용)
        scrollbar_detail = ttk.Scrollbar(right_frame, orient=tk.VERTICAL)
        self.detail_text = tk.Text(right_frame, yscrollcommand=scrollbar_detail.set, wrap=tk.WORD, width=40, state=tk.DISABLED)
        scrollbar_detail.config(command=self.detail_text.yview)
        
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_detail.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_config(self):
        """config.txt 파일에서 API 키 로드"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key.lower() == 'clientid':
                                self.digikey_api.client_id = value
                            elif key.lower() == 'clientsecret':
                                self.digikey_api.client_secret = value
                            elif key.lower() == 'usesandbox' or key.lower() == 'sandbox':
                                # 샌드박스 환경 설정 (기본값: False, 프로덕션)
                                self.digikey_api.use_sandbox = value.lower() in ('true', '1', 'yes')
                                self.digikey_api.base_url = (
                                    self.digikey_api.SANDBOX_BASE_URL 
                                    if self.digikey_api.use_sandbox 
                                    else self.digikey_api.PRODUCTION_BASE_URL
                                )
                            elif key.lower() == 'redirecturi':
                                # RedirectURI는 저장만 하고 사용하지 않음 (필요시 사용 가능)
                                pass
            except Exception as e:
                print(f"config 파일 읽기 오류: {str(e)}")
    
    def save_config(self, client_id, client_secret, use_sandbox=True):
        """config.txt 파일에 API 키 저장 (중복 방지)"""
        try:
            # 기존 config 파일 읽기
            config_data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # 중복 키 방지: 첫 번째 값만 사용
                            if key not in config_data:
                                config_data[key] = value
            
            # API 키 및 환경 설정 업데이트 (기존 값 덮어쓰기)
            config_data['ClientID'] = client_id
            config_data['ClientSecret'] = client_secret
            config_data['UseSandbox'] = 'true' if use_sandbox else 'false'
            
            # RedirectURI는 유지 (있는 경우)
            if 'RedirectURI' not in config_data:
                config_data['RedirectURI'] = 'https://localhost'
            
            # config 파일에 저장 (순서대로)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                # 주요 설정을 먼저 저장
                if 'ClientID' in config_data:
                    f.write(f"ClientID={config_data['ClientID']}\n")
                if 'ClientSecret' in config_data:
                    f.write(f"ClientSecret={config_data['ClientSecret']}\n")
                if 'RedirectURI' in config_data:
                    f.write(f"RedirectURI={config_data['RedirectURI']}\n")
                if 'UseSandbox' in config_data:
                    f.write(f"UseSandbox={config_data['UseSandbox']}\n")
        except Exception as e:
            print(f"config 파일 저장 오류: {str(e)}")
    
    def check_api_config(self):
        """디지키 API 설정 확인 및 자동 설정 다이얼로그 표시"""
        # API 설정 확인은 나중에 수행 (유저폼 이후)
        pass
    
    def show_initial_setup(self):
        """시작 시 엑셀 파일 및 시트 선택 유저폼 표시"""
        # 메인 윈도우를 뒤로 보내기
        self.root.lower()
        
        # 독립적인 윈도우로 생성
        setup_window = tk.Toplevel(self.root)
        setup_window.title("엑셀 파일 및 시트 선택")
        setup_window.geometry("500x300")
        setup_window.resizable(False, False)
        
        # 창 중앙 배치
        setup_window.update_idletasks()
        x = (setup_window.winfo_screenwidth() // 2) - (setup_window.winfo_width() // 2)
        y = (setup_window.winfo_screenheight() // 2) - (setup_window.winfo_height() // 2)
        setup_window.geometry(f"+{x}+{y}")
        
        # 모달 다이얼로그로 만들기
        setup_window.transient(self.root)
        setup_window.grab_set()
        setup_window.focus_set()
        setup_window.lift()
        setup_window.attributes('-topmost', True)  # 최상위로 설정
        setup_window.update()  # 강제 업데이트
        
        # 메인 프레임
        main_frame = ttk.Frame(setup_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="엑셀 파일 및 시트를 선택하세요", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 파일 선택 섹션
        file_frame = ttk.LabelFrame(main_frame, text="엑셀 파일", padding="10")
        file_frame.pack(fill=tk.X, pady=10)
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50, state="readonly")
        file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        def browse_file():
            filename = filedialog.askopenfilename(
                title="엑셀 파일 선택",
                filetypes=[
                    ("엑셀 통합문서", "*.xlsx"),
                    ("엑셀 매크로 포함 문서", "*.xlsm"),
                    ("엑셀 파일 (통합문서 및 매크로 포함)", "*.xlsx *.xlsm"),
                    ("엑셀 97-2003 통합문서", "*.xls"),
                    ("모든 엑셀 파일", "*.xlsx *.xlsm *.xls"),
                    ("모든 파일", "*.*")
                ]
            )
            if filename:
                self.file_path_var.set(filename)
                try:
                    self.excel_handler.load_file(filename)
                    sheets = self.excel_handler.get_sheet_names()
                    sheet_combo['values'] = sheets
                    if sheets:
                        sheet_var.set(sheets[0])
                except Exception as e:
                    messagebox.showerror("오류", f"파일 로드 중 오류가 발생했습니다:\n{str(e)}")
                    self.file_path_var.set("")
        
        ttk.Button(file_frame, text="찾아보기...", command=browse_file).pack(side=tk.LEFT, padx=5)
        
        # 시트 선택 섹션
        sheet_frame = ttk.LabelFrame(main_frame, text="시트 선택", padding="10")
        sheet_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(sheet_frame, text="시트:").pack(side=tk.LEFT, padx=5)
        
        sheet_var = tk.StringVar()
        sheet_combo = ttk.Combobox(sheet_frame, textvariable=sheet_var, state="readonly", width=40)
        sheet_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        def confirm_setup():
            file_path = self.file_path_var.get().strip()
            selected_sheet = sheet_var.get().strip()
            
            if not file_path:
                messagebox.showwarning("경고", "엑셀 파일을 선택해주세요.")
                return
            
            if not selected_sheet:
                messagebox.showwarning("경고", "시트를 선택해주세요.")
                return
            
            try:
                # 시트 로드
                self.current_df = self.excel_handler.load_sheet(selected_sheet)
                setup_window.destroy()
                # 메인 윈도우를 앞으로 가져오기
                self.root.lift()
                self.root.focus_force()
                # 데이터 표시
                self.finish_setup(selected_sheet)
                # 유저폼 완료 후 API 설정 확인
                self.check_api_config_after_setup()
            except Exception as e:
                messagebox.showerror("오류", f"시트 로드 중 오류가 발생했습니다:\n{str(e)}")
        
        def cancel_setup():
            if messagebox.askyesno("확인", "프로그램을 종료하시겠습니까?"):
                setup_window.destroy()
                self.root.quit()
        
        ttk.Button(button_frame, text="확인", command=confirm_setup, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=cancel_setup, width=15).pack(side=tk.LEFT, padx=5)
        
        # 파일 변경 시 시트 목록 업데이트
        def on_file_change(*args):
            if self.file_path_var.get():
                try:
                    sheets = self.excel_handler.get_sheet_names()
                    sheet_combo['values'] = sheets
                    if sheets:
                        sheet_var.set(sheets[0])
                except:
                    pass
        
        # 취소 버튼으로 창 닫기 방지 (확인 또는 취소 버튼만 사용)
        setup_window.protocol("WM_DELETE_WINDOW", cancel_setup)
    
    def finish_setup(self, sheet_name):
        """초기 설정 완료 후 실행"""
        if hasattr(self, 'sheet_label'):
            self.sheet_label.config(text=f"선택된 시트: {sheet_name}")
        if self.current_df is not None:
            self.display_sheet_data()
    
    def load_excel_file(self):
        """엑셀 파일 로드"""
        filename = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[
                ("엑셀 통합문서", "*.xlsx"),
                ("엑셀 매크로 포함 문서", "*.xlsm"),
                ("엑셀 파일 (통합문서 및 매크로 포함)", "*.xlsx *.xlsm"),
                ("엑셀 97-2003 통합문서", "*.xls"),
                ("모든 엑셀 파일", "*.xlsx *.xlsm *.xls"),
                ("모든 파일", "*.*")
            ]
        )
        
        if filename:
            try:
                self.excel_handler.load_file(filename)
                self.current_df = None
                messagebox.showinfo("성공", f"파일이 로드되었습니다: {filename}")
                self.select_sheet()
            except Exception as e:
                messagebox.showerror("오류", f"파일 로드 중 오류가 발생했습니다:\n{str(e)}")
    
    def select_sheet(self):
        """시트 선택 다이얼로그"""
        if not self.excel_handler.file_loaded():
            messagebox.showwarning("경고", "먼저 엑셀 파일을 열어주세요.")
            return
        
        sheets = self.excel_handler.get_sheet_names()
        if not sheets:
            messagebox.showwarning("경고", "사용 가능한 시트가 없습니다.")
            return
        
        # 시트 선택 다이얼로그
        sheet_window = tk.Toplevel(self.root)
        sheet_window.title("시트 선택")
        sheet_window.geometry("300x200")
        
        ttk.Label(sheet_window, text="시트를 선택하세요:").pack(pady=10)
        
        sheet_var = tk.StringVar(value=sheets[0])
        sheet_combo = ttk.Combobox(sheet_window, textvariable=sheet_var, values=sheets, state="readonly")
        sheet_combo.pack(pady=10)
        
        def load_sheet():
            selected_sheet = sheet_var.get()
            try:
                self.current_df = self.excel_handler.load_sheet(selected_sheet)
                self.sheet_label.config(text=f"선택된 시트: {selected_sheet}")
                self.display_sheet_data()
                sheet_window.destroy()
            except Exception as e:
                messagebox.showerror("오류", f"시트 로드 중 오류가 발생했습니다:\n{str(e)}")
        
        ttk.Button(sheet_window, text="확인", command=load_sheet).pack(pady=10)
    
    def display_sheet_data(self):
        """시트 데이터를 트리뷰에 표시"""
        if self.current_df is None or self.current_df.empty:
            return
        
        # 기존 항목 삭제
        for item in self.tree1.get_children():
            self.tree1.delete(item)
        
        # 컬럼 설정
        columns = list(self.current_df.columns)
        self.tree1["columns"] = columns
        self.tree1["show"] = "headings"
        
        # 헤더 설정
        for col in columns:
            self.tree1.heading(col, text=col)
            self.tree1.column(col, width=150, anchor=tk.W)
        
        # 데이터 삽입
        for index, row in self.current_df.iterrows():
            values = [str(val) for val in row.values]
            self.tree1.insert("", tk.END, values=values, iid=index)
    
    def on_part_double_click(self, event):
        """파트넘버 더블클릭 이벤트 처리"""
        selection = self.tree1.selection()
        if not selection:
            return
        
        # 선택된 행의 인덱스 가져오기
        selected_item = selection[0]
        try:
            row_index = int(selected_item)
        except ValueError:
            messagebox.showerror("오류", "행 인덱스를 가져올 수 없습니다.")
            return
        
        if self.current_df is None or row_index >= len(self.current_df):
            return
        
        # 파트넘버 컬럼 찾기 (대소문자 무시)
        part_number_col = self.find_part_number_column()
        
        if part_number_col is None:
            # 컬럼을 찾지 못한 경우 사용자에게 선택하게 함
            part_number_col = self.select_part_number_column()
            if part_number_col is None:
                return  # 사용자가 취소한 경우
        
        # 선택한 행부터 아래로 순환하며 조회
        self.query_parts_from_row(row_index, part_number_col)
    
    def find_part_number_column(self):
        """파트넘버 컬럼 자동 찾기"""
        if self.current_df is None or self.current_df.empty:
            return None
        
        # 다양한 패턴으로 파트넘버 컬럼 찾기
        possible_patterns = [
            # 정확한 매칭
            lambda col: 'part' in col.lower() and 'number' in col.lower(),
            # 파트넘버 (한글)
            lambda col: '파트' in col and '넘버' in col,
            lambda col: '파트' in col and '번호' in col,
            # Part Number (공백 포함)
            lambda col: col.lower().replace(' ', '') == 'partnumber',
            lambda col: col.lower().replace('_', '') == 'partnumber',
            # Part만 포함
            lambda col: col.lower() == 'part',
            lambda col: col.lower() == 'partno',
            lambda col: col.lower() == 'part_no',
            # Number만 포함 (일부 경우)
            lambda col: col.lower() == 'number' and 'part' not in col.lower(),
        ]
        
        for pattern in possible_patterns:
            for col in self.current_df.columns:
                if pattern(col):
                    return col
        
        return None
    
    def select_part_number_column(self):
        """사용자에게 파트넘버 컬럼 선택하게 함"""
        if self.current_df is None or self.current_df.empty:
            return None
        
        columns = list(self.current_df.columns)
        
        # 컬럼 선택 다이얼로그
        col_window = tk.Toplevel(self.root)
        col_window.title("파트넘버 컬럼 선택")
        col_window.geometry("350x200")
        col_window.transient(self.root)
        col_window.grab_set()
        col_window.focus_set()
        
        # 창 중앙 배치
        col_window.update_idletasks()
        x = (col_window.winfo_screenwidth() // 2) - (col_window.winfo_width() // 2)
        y = (col_window.winfo_screenheight() // 2) - (col_window.winfo_height() // 2)
        col_window.geometry(f"+{x}+{y}")
        
        ttk.Label(col_window, text="파트넘버 컬럼을 선택하세요:", font=("Arial", 10, "bold")).pack(pady=10)
        
        col_var = tk.StringVar()
        if columns:
            col_var.set(columns[0])
        
        col_combo = ttk.Combobox(col_window, textvariable=col_var, values=columns, state="readonly", width=30)
        col_combo.pack(pady=10)
        
        selected_col = [None]  # 리스트로 감싸서 클로저에서 수정 가능하게
        
        def confirm():
            selected_col[0] = col_var.get()
            col_window.destroy()
        
        def cancel():
            col_window.destroy()
        
        button_frame = ttk.Frame(col_window)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="확인", command=confirm, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=cancel, width=12).pack(side=tk.LEFT, padx=5)
        
        col_window.wait_window()  # 다이얼로그가 닫힐 때까지 대기
        
        return selected_col[0]
    
    def query_parts_from_row(self, start_row, part_number_col):
        """선택한 행부터 아래로 순환하며 파트넘버 조회"""
        if self.current_df is None:
            return
        
        query_results = []
        
        # 진행 상황 표시
        progress_window = tk.Toplevel(self.root)
        progress_window.title("조회 중...")
        progress_window.geometry("300x100")
        progress_label = ttk.Label(progress_window, text="파트넘버를 조회하고 있습니다...")
        progress_label.pack(pady=20)
        
        self.root.update()
        
        try:
            # 선택한 행부터 끝까지 순환
            for idx in range(start_row, len(self.current_df)):
                part_number = str(self.current_df.iloc[idx][part_number_col]).strip()
                
                # 빈 값 건너뛰기
                if not part_number or part_number == 'nan':
                    continue
                
                # 디지키 API로 조회
                try:
                    result = self.digikey_api.search_part(part_number)
                    if result:
                        query_results.append({
                            'Row': idx,
                            'PartNumber': part_number,
                            'Manufacturer': result.get('Manufacturer', 'N/A'),
                            'MountingType': result.get('MountingType', 'N/A'),
                            'FullData': result
                        })
                except Exception as e:
                    # API 오류 시에도 기본 정보는 추가
                    query_results.append({
                        'Row': idx,
                        'PartNumber': part_number,
                        'Manufacturer': '조회 실패',
                        'MountingType': '조회 실패',
                        'FullData': {'error': str(e)}
                    })
            
            self.query_results = query_results
            self.display_query_results()
            
            # 조회 탭으로 전환
            self.notebook.select(1)
            
            progress_window.destroy()
            messagebox.showinfo("완료", f"{len(query_results)}개의 파트넘버 조회가 완료되었습니다.")
            
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("오류", f"조회 중 오류가 발생했습니다:\n{str(e)}")
    
    def display_query_results(self):
        """조회 결과를 트리뷰에 표시"""
        # 기존 항목 삭제
        for item in self.tree2.get_children():
            self.tree2.delete(item)
        
        if not self.query_results:
            return
        
        # 컬럼 설정
        columns = ['Row', 'PartNumber', 'Manufacturer', 'MountingType']
        self.tree2["columns"] = columns
        self.tree2["show"] = "headings"
        
        # 헤더 설정
        self.tree2.heading('Row', text='Row')
        self.tree2.heading('PartNumber', text='파트넘버')
        self.tree2.heading('Manufacturer', text='제조업체')
        self.tree2.heading('MountingType', text='마운팅타입')
        
        # 컬럼 너비 설정
        self.tree2.column('Row', width=60, anchor=tk.CENTER)
        self.tree2.column('PartNumber', width=200, anchor=tk.W)
        self.tree2.column('Manufacturer', width=200, anchor=tk.W)
        self.tree2.column('MountingType', width=150, anchor=tk.W)
        
        # 데이터 삽입
        for i, result in enumerate(self.query_results):
            values = [
                str(result['Row']),
                result['PartNumber'],
                result['Manufacturer'],
                result['MountingType']
            ]
            self.tree2.insert("", tk.END, values=values, iid=i)
    
    def on_query_result_double_click(self, event):
        """조회 결과 더블클릭 시 상세정보 표시"""
        selection = self.tree2.selection()
        if not selection:
            return
        
        try:
            item_index = int(selection[0])
            if 0 <= item_index < len(self.query_results):
                result = self.query_results[item_index]
                self.display_detail_info(result)
        except (ValueError, IndexError) as e:
            messagebox.showerror("오류", f"상세정보를 가져올 수 없습니다: {str(e)}")
    
    def display_detail_info(self, result_data):
        """상세정보를 텍스트 위젯에 표시"""
        # 텍스트 위젯을 편집 가능하게 변경
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        
        full_data = result_data.get('FullData', {})
        
        # 기본 정보
        info_text = "=== 파트넘버 상세정보 ===\n\n"
        info_text += f"Row: {result_data.get('Row', 'N/A')}\n"
        info_text += f"파트넘버: {result_data.get('PartNumber', 'N/A')}\n"
        info_text += f"제조업체: {result_data.get('Manufacturer', 'N/A')}\n"
        info_text += f"마운팅타입: {result_data.get('MountingType', 'N/A')}\n\n"
        
        # 추가 정보가 있으면 표시
        if 'error' not in full_data:
            info_text += "--- 추가 정보 ---\n"
            for key, value in full_data.items():
                if key not in ['Manufacturer', 'MountingType']:  # 이미 표시한 항목 제외
                    # 딕셔너리나 리스트인 경우 문자열로 변환
                    if isinstance(value, dict):
                        value_str = ", ".join([f"{k}: {v}" for k, v in value.items()])
                        info_text += f"{key}: {value_str}\n"
                    elif isinstance(value, list):
                        value_str = ", ".join([str(v) for v in value])
                        info_text += f"{key}: {value_str}\n"
                    else:
                        info_text += f"{key}: {value}\n"
        else:
            info_text += f"\n오류: {full_data.get('error', '알 수 없는 오류')}\n"
        
        self.detail_text.insert(1.0, info_text)
        # 텍스트 위젯을 다시 읽기 전용으로 변경
        self.detail_text.config(state=tk.DISABLED)
    
    def check_api_config_after_setup(self):
        """유저폼 완료 후 API 설정 확인"""
        # config 파일에서 읽은 후에도 API 설정이 없을 때만 물어봄
        if not self.digikey_api.is_configured():
            # 메인 윈도우가 표시된 후 API 설정 안내
            self.root.after(300, self.show_api_settings_with_message)
    
    def show_api_settings_with_message(self):
        """API 설정 다이얼로그를 메시지와 함께 표시"""
        # 메인 윈도우가 표시되어 있는지 확인
        if not self.root.winfo_viewable():
            self.root.deiconify()
        
        response = messagebox.askyesno(
            "API 설정 필요",
            "디지키 API를 사용하려면 API 키를 설정해야 합니다.\n\n"
            "지금 설정하시겠습니까?\n\n"
            "(나중에 메뉴 > 설정 > 디지키 API 설정에서도 설정할 수 있습니다.)"
        )
        if response:
            self.show_api_settings()
    
    def show_api_settings(self):
        """디지키 API 설정 다이얼로그"""
        # 메인 윈도우가 표시되어 있는지 확인하고 표시
        if not self.root.winfo_viewable():
            self.root.deiconify()
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("디지키 API 설정")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()  # 모달 다이얼로그
        settings_window.focus_set()  # 포커스 설정
        settings_window.lift()  # 다른 창 위로 올리기
        
        # 창 중앙 배치
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
        y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        
        # 메인 프레임
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목 및 안내
        ttk.Label(main_frame, text="디지키 API 설정", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        ttk.Label(
            main_frame, 
            text="디지키 개발자 포털(developer.digikey.com)에서 받은\nClient ID와 Client Secret을 입력하세요.",
            justify=tk.CENTER,
            foreground="gray"
        ).pack(pady=(0, 10))
        
        # 환경 선택 (샌드박스/프로덕션)
        env_frame = ttk.Frame(main_frame)
        env_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(env_frame, text="환경:", width=15).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        env_var = tk.BooleanVar(value=self.digikey_api.use_sandbox)
        ttk.Radiobutton(env_frame, text="샌드박스", variable=env_var, value=True).grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Radiobutton(env_frame, text="프로덕션", variable=env_var, value=False).grid(row=0, column=2, padx=5, sticky=tk.W)
        
        ttk.Label(
            main_frame, 
            text="※ 샌드박스 키는 샌드박스 환경, 프로덕션 키는 프로덕션 환경을 선택하세요",
            justify=tk.CENTER,
            foreground="red",
            font=("Arial", 8)
        ).pack(pady=(0, 10))
        
        # 입력 프레임
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(input_frame, text="Client ID:", width=15).grid(row=0, column=0, padx=5, pady=10, sticky=tk.W)
        client_id_entry = ttk.Entry(input_frame, width=35)
        client_id_entry.grid(row=0, column=1, padx=5, pady=10, sticky=(tk.W, tk.E))
        if self.digikey_api.client_id:
            client_id_entry.insert(0, self.digikey_api.client_id)
        
        ttk.Label(input_frame, text="Client Secret:", width=15).grid(row=1, column=0, padx=5, pady=10, sticky=tk.W)
        client_secret_entry = ttk.Entry(input_frame, width=35, show="*")
        client_secret_entry.grid(row=1, column=1, padx=5, pady=10, sticky=(tk.W, tk.E))
        if self.digikey_api.client_secret:
            client_secret_entry.insert(0, self.digikey_api.client_secret)
        
        input_frame.columnconfigure(1, weight=1)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=30, fill=tk.X)
        
        def save_settings():
            client_id = client_id_entry.get().strip()
            client_secret = client_secret_entry.get().strip()
            use_sandbox = env_var.get()
            
            if client_id and client_secret:
                self.digikey_api.set_credentials(client_id, client_secret)
                self.digikey_api.use_sandbox = use_sandbox
                self.digikey_api.base_url = (
                    self.digikey_api.SANDBOX_BASE_URL 
                    if use_sandbox 
                    else self.digikey_api.PRODUCTION_BASE_URL
                )
                # config 파일에 저장
                self.save_config(client_id, client_secret, use_sandbox)
                messagebox.showinfo("성공", "API 설정이 저장되었습니다.\nconfig.txt 파일에도 저장되었습니다.")
                settings_window.destroy()
            else:
                messagebox.showwarning("경고", "Client ID와 Client Secret을 모두 입력해주세요.")
        
        # 저장 버튼 (더 눈에 띄게)
        save_btn = ttk.Button(button_frame, text="저장", command=save_settings, width=18)
        save_btn.pack(side=tk.LEFT, padx=10, expand=True)
        
        # 취소 버튼
        cancel_btn = ttk.Button(button_frame, text="취소", command=settings_window.destroy, width=18)
        cancel_btn.pack(side=tk.LEFT, padx=10, expand=True)
    
    def on_closing(self):
        """프로그램 종료 처리"""
        # 열려있는 모든 Toplevel 윈도우 닫기
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                try:
                    widget.destroy()
                except:
                    pass
        
        # 메인 윈도우 종료
        self.root.quit()
        self.root.destroy()


def main():
    """메인 함수"""
    root = tk.Tk()
    app = DigikeyViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
