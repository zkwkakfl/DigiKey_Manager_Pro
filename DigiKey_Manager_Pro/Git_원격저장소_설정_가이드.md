# Git 원격 저장소 설정 가이드

## 현재 상태
- 로컬 Git 저장소에 커밋 및 태그가 저장되어 있습니다.
- 원격 저장소가 설정되어 있지 않습니다.

## 원격 저장소에 푸시하는 방법

### 방법 1: GitHub 사용 (권장)

#### 1단계: GitHub에서 저장소 생성
1. [GitHub](https://github.com)에 로그인
2. 우측 상단의 "+" 버튼 클릭 → "New repository" 선택
3. 저장소 이름 입력 (예: `DigiKey_Manager_Pro`)
4. Public 또는 Private 선택
5. **"Initialize this repository with a README" 체크 해제** (이미 로컬에 파일이 있으므로)
6. "Create repository" 클릭

#### 2단계: 원격 저장소 추가 및 푸시
```bash
# 원격 저장소 추가 (YOUR_USERNAME과 YOUR_REPO_NAME을 실제 값으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 또는 SSH 사용 시
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git

# 모든 브랜치와 태그 푸시
git push -u origin master
git push --tags
```

### 방법 2: GitLab 사용

#### 1단계: GitLab에서 프로젝트 생성
1. [GitLab](https://gitlab.com)에 로그인
2. "New project" 클릭
3. "Create blank project" 선택
4. 프로젝트 이름 입력
5. Visibility 선택
6. "Create project" 클릭

#### 2단계: 원격 저장소 추가 및 푸시
```bash
# 원격 저장소 추가
git remote add origin https://gitlab.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 푸시
git push -u origin master
git push --tags
```

### 방법 3: 기존 원격 저장소가 있는 경우

```bash
# 원격 저장소 확인
git remote -v

# 원격 저장소가 이미 있다면 바로 푸시
git push -u origin master
git push --tags
```

## 주의사항

### .gitignore 확인
- `config.txt`, `token.json` 등 민감한 정보는 .gitignore에 포함되어 있습니다.
- 이 파일들은 원격 저장소에 푸시되지 않습니다.

### 푸시 전 확인사항
1. 민감한 정보가 코드에 하드코딩되어 있지 않은지 확인
2. API 키나 비밀번호가 코드에 포함되어 있지 않은지 확인
3. `.gitignore` 파일이 올바르게 설정되어 있는지 확인

## 빠른 명령어 (GitHub 예시)

```bash
# 1. 원격 저장소 추가 (GitHub 저장소 URL로 변경)
git remote add origin https://github.com/YOUR_USERNAME/DigiKey_Manager_Pro.git

# 2. 현재 브랜치 푸시
git push -u origin master

# 3. 모든 태그 푸시
git push --tags

# 4. 확인
git remote -v
```

## 문제 해결

### 인증 오류 발생 시
- GitHub: Personal Access Token 사용 필요
- GitLab: Personal Access Token 또는 SSH 키 사용

### 푸시 거부 시
```bash
# 강제 푸시 (주의: 다른 사람과 공유하는 저장소에서는 사용하지 마세요)
git push -u origin master --force
```

## 다음 단계
원격 저장소 URL을 알려주시면 바로 설정해드리겠습니다!
