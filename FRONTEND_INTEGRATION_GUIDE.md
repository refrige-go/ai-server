# 프론트엔드-백엔드 연동 가이드

## 1. API 엔드포인트

백엔드는 다음과 같은 API 엔드포인트를 제공합니다:

### 1.1 OCR API
- **엔드포인트**: `/api/recipes/ocr`
- **메서드**: POST
- **요청**: 
  - Content-Type: multipart/form-data
  - Body: image (파일)
- **응답**: 
  ```json
  {
    "ingredients": [
      {
        "name": "string",
        "confidence": "float"
      }
    ]
  }
  ```

### 1.2 시맨틱 검색 API
- **엔드포인트**: `/api/recipes/search`
- **메서드**: POST
- **요청**: 
  ```json
  {
    "query": "string",
    "searchType": "recipe|ingredient"
  }
  ```
- **응답**: 
  ```json
  {
    "recipes": [
      {
        "recipe_id": "string",
        "name": "string",
        "score": "float",
        "match_reason": "string"
      }
    ],
    "ingredients": [
      {
        "ingredient_id": "string",
        "name": "string",
        "score": "float",
        "match_reason": "string"
      }
    ]
  }
  ```

### 1.3 레시피 추천 API
- **엔드포인트**: `/api/recipes/recommendation`
- **메서드**: POST
- **요청**: 
  ```json
  {
    "preferences": {
      "ingredients": ["string"],
      "categories": ["string"],
      "weather": {
        "temperature": "float",
        "condition": "string"
      }
    }
  }
  ```
- **응답**: 
  ```json
  {
    "recipes": [
      {
        "recipe_id": "string",
        "name": "string",
        "match_reason": "string"
      }
    ]
  }
  ```

## 2. API 클라이언트 설정

### 2.1 환경 변수 설정
`.env.local` 파일에 다음 설정을 추가:
```
NEXT_PUBLIC_BASE_API_URL=http://localhost:8080
```

### 2.2 Axios 인스턴스 설정
`src/api/axiosInstance.jsx` 파일이 이미 구현되어 있으므로 추가 설정 불필요.

## 3. API 호출 구현

### 3.1 OCR 처리
```javascript
// src/api/recipeApi.js
export const recipeApi = {
  processOCR: async (imageFile) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    const response = await axiosInstance.post('/api/recipes/ocr', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  }
};
```

### 3.2 시맨틱 검색
```javascript
// src/api/recipeApi.js
export const recipeApi = {
  semanticSearch: async (query, searchType) => {
    const response = await axiosInstance.post('/api/recipes/search', {
      query,
      searchType
    });
    return response.data;
  }
};
```

### 3.3 레시피 추천
```javascript
// src/api/recipeApi.js
export const recipeApi = {
  getRecommendation: async (preferences) => {
    const response = await axiosInstance.post('/api/recipes/recommendation', {
      preferences
    });
    return response.data;
  }
};
```

## 4. 컴포넌트 구현

### 4.1 OCR 컴포넌트
```javascript
// src/components/OCRUpload.jsx
const OCRUpload = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    try {
      setLoading(true);
      const response = await recipeApi.processOCR(file);
      setResult(response);
    } catch (error) {
      console.error('OCR 처리 중 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? '처리 중...' : '업로드'}
      </button>
      {result && (
        <div>
          <h3>인식된 식재료:</h3>
          <ul>
            {result.ingredients.map((ingredient, index) => (
              <li key={index}>
                {ingredient.name} (신뢰도: {ingredient.confidence})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

### 4.2 검색 컴포넌트
```javascript
// src/components/SearchBar.jsx
const SearchBar = () => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('recipe');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    try {
      setLoading(true);
      const response = await recipeApi.semanticSearch(query, searchType);
      setResults(response);
    } catch (error) {
      console.error('검색 중 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="검색어를 입력하세요"
      />
      <select value={searchType} onChange={(e) => setSearchType(e.target.value)}>
        <option value="recipe">레시피</option>
        <option value="ingredient">식재료</option>
      </select>
      <button onClick={handleSearch} disabled={!query || loading}>
        {loading ? '검색 중...' : '검색'}
      </button>
      {results && (
        <div>
          {/* 검색 결과 표시 */}
        </div>
      )}
    </div>
  );
};
```

## 5. 에러 처리

### 5.1 공통 에러 처리
```javascript
// src/utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.response) {
    // 서버 응답이 있는 경우
    console.error('API 에러:', error.response.data);
    return error.response.data;
  } else if (error.request) {
    // 요청은 보냈지만 응답이 없는 경우
    console.error('네트워크 에러:', error.request);
    return { message: '서버와 통신할 수 없습니다.' };
  } else {
    // 요청 설정 중 에러가 발생한 경우
    console.error('요청 에러:', error.message);
    return { message: '요청을 처리할 수 없습니다.' };
  }
};
```

### 5.2 토큰 만료 처리
`axiosInstance.jsx`에 이미 구현되어 있음.

## 6. 상태 관리

### 6.1 React Query 사용
```javascript
// src/hooks/useRecipes.js
import { useQuery, useMutation } from '@tanstack/react-query';
import { recipeApi } from '../api/recipeApi';

export const useRecipes = () => {
  const searchRecipes = useMutation({
    mutationFn: ({ query, searchType }) => 
      recipeApi.semanticSearch(query, searchType)
  });

  const getRecommendations = useMutation({
    mutationFn: (preferences) => 
      recipeApi.getRecommendation(preferences)
  });

  return {
    searchRecipes,
    getRecommendations
  };
};
```

## 7. UI/UX 고려사항

### 7.1 로딩 상태
- 모든 API 호출에 로딩 상태 표시
- 스켈레톤 UI 사용

### 7.2 에러 메시지
- 사용자 친화적인 에러 메시지
- 재시도 옵션 제공

### 7.3 반응형 디자인
- 모바일 환경 고려
- 이미지 업로드 UI 최적화

## 8. 테스트

### 8.1 단위 테스트
- API 호출 함수 테스트
- 컴포넌트 테스트

### 8.2 통합 테스트
- API 연동 테스트
- 사용자 시나리오 테스트

## 9. 성능 최적화

### 9.1 이미지 최적화
- 이미지 크기 제한
- 압축 처리

### 9.2 캐싱
- React Query 캐싱 활용
- 검색 결과 캐싱

## 10. 보안

### 10.1 입력 검증
- 파일 형식 검증
- 검색어 검증

### 10.2 XSS 방지
- 입력값 이스케이프
- 안전한 HTML 렌더링 