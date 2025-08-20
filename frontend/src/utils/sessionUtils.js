// 세션 ID 암호화/복호화 유틸리티
// 실제 프로덕션에서는 더 강력한 암호화를 사용해야 합니다

// 세션 ID 유효성 검증
export const validateSessionId = (sessionId) => {
  if (!sessionId || typeof sessionId !== 'string') {
    return false;
  }
  
  // UUID 형식 검증
  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidPattern.test(sessionId);
};

// 간단한 Base64 인코딩 (실제로는 더 강력한 암호화 사용 권장)
export const encodeSessionId = (sessionId) => {
  try {
    // 세션 ID 유효성 검증
    if (!validateSessionId(sessionId)) {
      console.error('유효하지 않은 세션 ID:', sessionId);
      return null;
    }
    return btoa(sessionId);
  } catch (error) {
    console.error('세션 ID 인코딩 실패:', error);
    return null;
  }
};

export const decodeSessionId = (encodedSessionId) => {
  try {
    const decodedSessionId = atob(encodedSessionId);
    
    // 디코딩된 세션 ID 유효성 검증
    if (!validateSessionId(decodedSessionId)) {
      console.error('디코딩된 세션 ID가 유효하지 않음:', decodedSessionId);
      return null;
    }
    
    return decodedSessionId;
  } catch (error) {
    console.error('세션 ID 디코딩 실패:', error);
    return null;
  }
};

// URL에서 세션 ID 추출 (암호화된 형태 지원)
export const extractSessionIdFromUrl = (search) => {
  if (!search) return null;

  const urlParams = new URLSearchParams(search);

  // 1) 우선 암호화된 파라미터 지원 (?sessionId=BASE64)
  const encodedSessionId = urlParams.get('sessionId');
  if (encodedSessionId) {
    const decoded = decodeSessionId(encodedSessionId);
    if (decoded) return decoded;
    console.error('URL에서 유효하지 않은 암호화된 세션 ID 추출됨');
  }

  // 2) 과거/직접 링크 호환 (?session=UUID)
  const rawSessionId = urlParams.get('session');
  if (rawSessionId && validateSessionId(rawSessionId)) {
    return rawSessionId;
  }

  return null;
};

// 세션 ID를 URL 파라미터로 변환
export const createSessionUrl = (sessionId) => {
  const encodedSessionId = encodeSessionId(sessionId);
  if (!encodedSessionId) {
    console.error('세션 ID 인코딩 실패로 URL 생성 불가');
    return '/result';
  }
  return `/result?sessionId=${encodedSessionId}`;
};