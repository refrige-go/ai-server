# AI 서버 설치 및 실행 가이드

## 1. Python 설치

### 1.1 Windows
1. [Python 공식 웹사이트](https://www.python.org/downloads/)에서 Python 3.10 이상 버전 다운로드
2. 설치 시 "Add Python to PATH" 옵션 체크
3. 설치 완료 후 명령 프롬프트에서 다음 명령어로 설치 확인:
   ```bash
   python --version
   pip --version
   ```

### 1.2 macOS
1. [Homebrew](https://brew.sh/) 설치 (터미널에서):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Python 설치:
   ```bash
   brew install python@3.10
   ```
3. 설치 확인:
   ```bash
   python3 --version
   pip3 --version
   ```

## 2. 프로젝트 설정

### 2.1 저장소 클론
```bash
git clone https://github.com/refrige-go/ai-server.git
cd ai-server
```

### 2.2 가상환경 생성 및 활성화

#### Windows
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate
```

#### macOS/Linux
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate
```

### 2.3 의존성 설치
```bash
pip install -r requirements.txt
```

## 3. 환경 변수 설정

### 3.1 .env 파일 생성
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key

# OpenSearch 설정
OPENSEARCH_HOST=your_opensearch_host
OPENSEARCH_USER=your_username
OPENSEARCH_PASSWORD=your_password

# Google Cloud Vision 설정
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### 3.2 API 키 발급
1. **OpenAI API 키**
   - [OpenAI Platform](https://platform.openai.com/)에서 계정 생성
   - API 키 발급

2. **Google Cloud Vision API 키**
   - [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
   - Vision API 활성화
   - 서비스 계정 생성 및 키 파일 다운로드

3. **OpenSearch 접속 정보**
   - OpenSearch 클러스터 호스트
   - 사용자 이름
   - 비밀번호

## 4. 데이터 준비

### 4.1 데이터 접근
프로젝트의 데이터는 이미 준비되어 있으며, 다음 위치에서 확인할 수 있습니다:

1. **OpenSearch 데이터**
   - 이미 업로드되어 있으므로 추가 작업 불필요
   - OpenSearch 클러스터: `your-opensearch-host`
   - 인덱스: `recipes`, `ingredients`

2. **임베딩 데이터**
   - 위치: `data/` 디렉토리
   - 파일:
     - `recipe_embeddings.json`
     - `ingredient_embeddings.json`
     - `synonym_dictionary.json`
   - 이 파일들은 이미 프로젝트에 포함되어 있으므로 추가 다운로드 불필요

> **참고**: 데이터 업로드나 임베딩 생성은 일회성 작업으로, 이미 완료되어 있습니다. 다른 개발자들은 이 단계를 건너뛰고 바로 서버 실행으로 넘어가시면 됩니다.

## 5. 서버 실행

### 5.1 개발 모드
```bash
uvicorn app.main:app --reload
```

### 5.2 프로덕션 모드
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 6. API 테스트

### 6.1 Swagger UI
브라우저에서 다음 URL 접속:
```
http://localhost:8000/docs
```

### 6.2 테스트 스크립트 실행
```bash
python scripts/test_search.py
```

## 7. 문제 해결

### 7.1 일반적인 문제
1. **가상환경 활성화 실패**
   - Windows: PowerShell 실행 정책 변경
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```
   - macOS/Linux: 실행 권한 확인
     ```bash
     chmod +x venv/bin/activate
     ```

2. **의존성 설치 실패**
   - pip 업그레이드:
     ```bash
     python -m pip install --upgrade pip
     ```
   - 개별 패키지 설치:
     ```bash
     pip install package_name
     ```

3. **OpenSearch 연결 실패**
   - 호스트 및 인증 정보 확인
   - 방화벽 설정 확인
   - SSL 인증서 확인

### 7.2 로그 확인
- 서버 로그: `logs/app.log`
- 에러 로그: `logs/error.log`

## 8. 개발 도구

### 8.1 VS Code 설정
1. Python 확장 설치
2. 가상환경 선택
3. Python 린터 설정

### 8.2 디버깅
1. VS Code 디버깅 설정
2. 브레이크포인트 설정
3. 변수 검사

## 9. 추가 리소스

### 9.1 문서
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [OpenSearch 문서](https://opensearch.org/docs/)
- [OpenAI API 문서](https://platform.openai.com/docs/api-reference)

### 9.2 커뮤니티
- [FastAPI GitHub](https://github.com/tiangolo/fastapi)
- [OpenSearch GitHub](https://github.com/opensearch-project/OpenSearch)
- [OpenAI Community](https://community.openai.com/) 