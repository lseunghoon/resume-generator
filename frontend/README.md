# sseojum Frontend

AI 기반 자기소개서 생성 서비스의 프론트엔드 애플리케이션입니다.

## 주요 변경사항 (v2.0)

### 🚀 새로운 기능
- **직접 입력 방식**: 채용정보를 직접 입력하여 더 정확한 자기소개서 생성
- **향상된 UI/UX**: 모던하고 직관적인 사용자 인터페이스
- **반응형 디자인**: 모바일과 데스크톱 모두 지원

### 🔄 변경된 플로우
- **크롤링 제거**: URL 입력 방식에서 직접 입력 방식으로 전환
- **단계별 입력**: 채용정보 → 파일 업로드 → 질문 답변 → 결과 확인
- **실시간 검증**: 입력 필드별 실시간 유효성 검사

## 기술 스택

- **Framework**: React 18
- **Routing**: React Router v6
- **Styling**: CSS3 (모던 디자인)
- **Build Tool**: Create React App
- **Package Manager**: npm

## 설치 및 실행

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
REACT_APP_API_URL=http://localhost:5000
```

### 3. 개발 서버 실행

```bash
npm start
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

## 사용자 플로우

### 1. 채용정보 입력
- 회사명, 직무, 주요업무, 자격요건, 우대사항 입력
- 실시간 유효성 검사
- 필수 필드 검증

### 2. 이력서 업로드
- PDF, DOCX 파일 업로드 지원
- 드래그 앤 드롭 기능
- 파일 크기 및 형식 검증

### 3. 자기소개서 생성
- AI 기반 자기소개서 자동 생성
- 질문별 개별 답변 생성
- 실시간 생성 상태 표시

### 4. 결과 확인 및 수정
- 생성된 자기소개서 확인
- 수정 요청 기능
- 버전 히스토리 관리

## 페이지 구조

```
src/
├── pages/
│   ├── JobInfoInputPage.jsx    # 채용정보 입력 페이지
│   ├── FileUploadPage.jsx      # 파일 업로드 페이지
│   ├── QuestionPage.jsx        # 질문 답변 페이지
│   └── ResultPage.jsx          # 결과 확인 페이지
├── components/
│   ├── Header.jsx              # 헤더 컴포넌트
│   ├── Navigation.jsx          # 네비게이션 컴포넌트
│   ├── Button.jsx              # 버튼 컴포넌트
│   └── Input.jsx               # 입력 컴포넌트
├── services/
│   └── api.js                  # API 통신 서비스
└── hooks/
    └── useGenerate.js          # 자기소개서 생성 훅
```

## API 통신

### 주요 API 엔드포인트
- `POST /api/v1/job-info` - 채용정보 입력
- `POST /api/v1/upload` - 파일 업로드
- `POST /api/v1/generate` - 자기소개서 생성
- `POST /api/v1/revise` - 자기소개서 수정

### 에러 처리
- 네트워크 오류 처리
- 사용자 친화적인 오류 메시지
- 재시도 기능

## 스타일링

### 디자인 시스템
- 일관된 색상 팔레트
- 반응형 그리드 시스템
- 모던한 타이포그래피

### 컴포넌트 스타일
- CSS 모듈 사용
- 재사용 가능한 컴포넌트
- 접근성 고려

## 개발 가이드

### 코드 스타일
- ESLint 규칙 준수
- 함수형 컴포넌트 사용
- Hooks 기반 상태 관리

### 성능 최적화
- React.memo 사용
- 불필요한 리렌더링 방지
- 코드 스플리팅

## 배포

### 프로덕션 빌드

```bash
npm run build
```

### 정적 호스팅

```bash
# Netlify 배포
netlify deploy --prod --dir=build

# Vercel 배포
vercel --prod
```

## 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
