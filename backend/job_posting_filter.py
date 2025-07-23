import logging
import re
from typing import Optional, Tuple
from vertex_client import model  # vertex_client.py에서 초기화된 모델 사용

logger = logging.getLogger(__name__)

class JobPostingFilter:
    """채용공고 텍스트 필터링 및 검증 클래스"""
    
    # 채용공고 관련 키워드들 (확장된 버전)
    JOB_POSTING_KEYWORDS = {
        'required': [
            '모집', '채용', '지원', '근무', '업무', '직무', '자격', '요구사항', 
            '우대사항', '담당업무', '주요업무', '근무조건', '급여', '연봉', '회사',
            '지원자격', '전형절차', '면접', '서류전형', '경력', '신입', '경험',
            '스킬', '기술', '역량', '능력', '학력', '전공', '복리후생', '혜택',
            # 영문 키워드 추가
            'recruit', 'hiring', 'job', 'position', 'career', 'work', 'company',
            'requirement', 'qualification', 'experience', 'skill', 'salary',
            # 추가 한국어 키워드
            '인재', '사원', '직원', '팀원', '동료', '포지션', '직책', '직위',
            '입사', '취업', '구직', '구인', '인력', '선발', '채용공고',
            '지원서', '이력서', '포트폴리오', '프로젝트', '개발', '운영', '관리',
            # 링커리어/대학생 특화 키워드
            '대학생', '신입생', '졸업생', '학생', '인턴', '인턴십', '신입', '준비',
            '지원', '활동', '프로그램', '교육', '트레이닝', '성장', '기회',
            '스타트업', '기업', '조직', '부서', '팀', '직무', '역할', '담당',
            '링커리어', 'linkareer', '공고', '모집요강', '지원요강'
        ],
        'company_info': [
            '회사소개', '기업정보', '사업분야', '조직', '팀', '부서', '본사', '지사',
            '설립', '매출', '직원수', '기업문화', '비전', '미션', '가치',
            # 영문 추가
            'company', 'organization', 'team', 'business', 'mission', 'vision'
        ],
        'application': [
            '지원방법', '접수방법', '제출서류', '마감일', '전형일정', '연락처',
            '문의', '담당자', '이메일', '전화번호', '홈페이지', 'URL',
            # 영문 추가
            'apply', 'application', 'contact', 'email', 'phone'
        ]
    }
    
    # 불필요한 섹션 키워드들 (매우 제한적으로)
    NOISE_KEYWORDS = [
        '광고', '배너', '추천채용', '관련채용', '유사채용', '다른채용', '인기채용',
        '최신채용', '베스트채용', 'HOT채용', '추천기업', '관련기업', '유사기업',
        '마이페이지', '즐겨찾기', '공유하기', '프린트',
        '상단으로', '하단으로', '이전페이지', '다음페이지', '목록으로', '검색',
        '필터', '정렬', '카테고리', '메뉴', '네비게이션', '푸터', '헤더',
        '쿠키', '개인정보', '이용약관', '고객센터', '문의하기', 'FAQ',
        '댓글', '좋아요', '공감', '스크랩', '북마크'
    ]

    @classmethod
    def filter_job_posting_content(cls, raw_text: str) -> Optional[str]:
        """크롤링된 원본 텍스트에서 채용공고 관련 내용만 필터링"""
        try:
            if not raw_text or len(raw_text.strip()) < 50:
                logger.warning("텍스트가 너무 짧습니다.")
                return None
            
            # 1단계: 기본 전처리
            cleaned_text = cls._preprocess_text(raw_text)
            
            # 2단계: 노이즈 제거 (완화된 버전)
            noise_removed_text = cls._remove_noise_sections_improved(cleaned_text)
            
            # 3단계: 키워드 기반 검증
            keyword_score = cls._calculate_keyword_score(noise_removed_text)
            
            # 디버깅: 크롤링된 텍스트 내용 로그 (처음 500자)
            logger.info(f"크롤링된 텍스트 미리보기 (500자): {noise_removed_text[:500]}...")
            logger.info(f"전체 텍스트 길이: {len(noise_removed_text)}자")
            
            # 텍스트가 있는 경우 우선 반환 (우회 로직 강화)
            if len(noise_removed_text.strip()) > 200:
                logger.info("텍스트가 충분히 있어 키워드 검증 건너뛰고 바로 통과")
                return noise_removed_text
            
            # 텍스트가 너무 적은 경우에만 AI 검증
            if len(noise_removed_text.strip()) < 200:
                logger.warning("텍스트가 부족하여 AI 검증 시도")
                ai_filtered = cls._ai_filter_job_posting(noise_removed_text)
                return ai_filtered if ai_filtered else None
            
            return noise_removed_text
                
        except Exception as e:
            logger.error(f"채용공고 필터링 중 오류: {e}")
            # 오류 발생 시 기본 전처리만 된 텍스트 반환
            try:
                return cls._preprocess_text(raw_text)
            except:
                return raw_text

    @classmethod
    def _preprocess_text(cls, text: str) -> str:
        """기본 텍스트 전처리"""
        # 과도한 공백 및 특수문자 정리
        text = re.sub(r'\s+', ' ', text)  # 연속된 공백을 하나로
        text = re.sub(r'[\r\n]+', '\n', text)  # 연속된 줄바꿈을 하나로
        
        # 너무 짧은 줄들만 제거 (2글자 미만)
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 2]
        
        return '\n'.join(lines)

    @classmethod
    def _remove_noise_sections_improved(cls, text: str) -> str:
        """개선된 노이즈 섹션 제거 - 매우 보수적으로 제거"""
        lines = text.split('\n')
        filtered_lines = []
        
        # 채용공고 키워드가 있는 줄은 절대 제거하지 않음
        job_keywords = set()
        for category in cls.JOB_POSTING_KEYWORDS.values():
            job_keywords.update([kw.lower() for kw in category])
        
        for line in lines:
            line_lower = line.lower()
            line_stripped = line.strip()
            
            # 빈 줄 제거
            if len(line_stripped) == 0:
                continue
            
            # 채용공고 관련 키워드가 있는 줄은 절대 제거하지 않음
            has_job_keyword = any(kw in line_lower for kw in job_keywords)
            if has_job_keyword:
                filtered_lines.append(line)
                continue
            
            # 매우 명확한 노이즈만 제거
            is_clear_noise = False
            
            # 1. 명확한 네비게이션/메뉴만 제거
            clear_noise_patterns = [
                r'^로그인$', r'^회원가입$', r'^마이페이지$', r'^장바구니$',
                r'^홈$', r'^메뉴$', r'^검색$', r'^필터$', r'^정렬$',
                r'^이전$', r'^다음$', r'^목록$', r'^상단으로$', r'^하단으로$',
                r'^쿠키정책$', r'^개인정보처리방침$', r'^이용약관$',
                r'^[\s\-_=.]{3,}$',  # 단순 구분선
                r'^[0-9]{1,2}$',     # 단순 숫자만
                r'^[,.()!@#$%^&*]{1,3}$'  # 단순 특수문자만
            ]
            
            for pattern in clear_noise_patterns:
                if re.match(pattern, line_stripped):
                    is_clear_noise = True
                    break
            
            # 2. 너무 짧고 의미 없는 줄만 제거 (1글자)
            if len(line_stripped) == 1 and line_stripped.isalnum():
                is_clear_noise = True
            
            if not is_clear_noise:
                filtered_lines.append(line)
        
        # 결과 확인
        original_length = len(text)
        filtered_text = '\n'.join(filtered_lines)
        filtered_length = len(filtered_text)
        
        logger.info(f"개선된 노이즈 제거: {original_length}자 → {filtered_length}자 ({len(lines)}줄 → {len(filtered_lines)}줄)")
        
        # 너무 많이 제거된 경우 원본 텍스트의 70% 이상 유지
        if filtered_length < original_length * 0.7:
            logger.warning("노이즈 제거로 너무 많은 내용이 삭제됨. 더 관대한 필터링 적용")
            return cls._gentle_noise_removal(text)
        
        return filtered_text

    @classmethod
    def _gentle_noise_removal(cls, text: str) -> str:
        """매우 관대한 노이즈 제거 - 최소한만 제거"""
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # 완전히 비어있는 줄만 제거
            if len(line_stripped) == 0:
                continue
            
            # 명백한 HTML 태그나 스크립트만 제거
            if re.match(r'^<[^>]+>$', line_stripped) or 'javascript:' in line_stripped.lower():
                continue
            
            filtered_lines.append(line)
        
        result = '\n'.join(filtered_lines)
        logger.info(f"관대한 노이즈 제거: {len(text)}자 → {len(result)}자")
        return result

    @classmethod
    def _calculate_keyword_score(cls, text: str) -> float:
        """채용공고 관련 키워드 스코어 계산"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        
        # 각 카테고리별 키워드 매칭 점수 계산
        required_matches = sum(1 for keyword in cls.JOB_POSTING_KEYWORDS['required'] 
                             if keyword in text_lower)
        company_matches = sum(1 for keyword in cls.JOB_POSTING_KEYWORDS['company_info'] 
                            if keyword in text_lower)
        application_matches = sum(1 for keyword in cls.JOB_POSTING_KEYWORDS['application'] 
                                if keyword in text_lower)
        
        # 가중치 적용 스코어 계산
        total_keywords = (len(cls.JOB_POSTING_KEYWORDS['required']) + 
                         len(cls.JOB_POSTING_KEYWORDS['company_info']) + 
                         len(cls.JOB_POSTING_KEYWORDS['application']))
        
        if total_keywords == 0:
            return 0.0
        
        weighted_score = (required_matches * 2 + company_matches + application_matches) / (total_keywords * 1.5)
        
        return min(weighted_score, 1.0)  # 최대 1.0으로 제한

    @classmethod
    def _ai_filter_job_posting(cls, text: str) -> Optional[str]:
        """AI 모델을 사용하여 채용공고 내용만 추출"""
        try:
            if not text or len(text.strip()) < 10:
                return None
                
            prompt = f"""다음 텍스트에서 채용공고와 관련된 내용만을 추출하여 정리해주세요.

## 추출할 내용:
- 회사 소개 및 사업 분야
- 모집 직무/포지션
- 주요 업무 및 담당 업무
- 지원 자격 및 요구사항
- 우대사항
- 근무 조건 (근무지, 근무시간, 고용형태 등)
- 급여 및 복리후생
- 전형 절차 및 지원 방법

## 제외할 내용:
- 웹사이트 네비게이션 메뉴
- 광고 및 배너
- 관련/추천 채용공고 링크
- 댓글이나 리뷰
- 로그인/회원가입 관련 텍스트
- 쿠키/개인정보 정책

텍스트가 채용공고가 아니라면 "채용공고가 아닙니다"라고 응답해주세요.

원본 텍스트:
{text}

채용공고 내용만 정리:"""

            response = model.generate_content(prompt)
            result = response.text.strip()
            
            # AI가 채용공고가 아니라고 판단한 경우
            if "채용공고가 아닙니다" in result or len(result) < 100:
                logger.info("AI 모델이 채용공고가 아니라고 판단함")
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"AI 필터링 실패: {e}")
            return None

    @classmethod
    def validate_job_posting(cls, text: str) -> Tuple[bool, float, str]:
        """채용공고 텍스트의 유효성 검증 (OCR 텍스트 지원)"""
        try:
            if not text or len(text.strip()) < 20:
                return False, 0.0, "텍스트가 너무 짧습니다"
            
            text_lower = text.lower()
            
            # OCR 텍스트인지 확인
            is_ocr_text = "이미지에서 추출된 콘텐츠" in text
            
            if is_ocr_text:
                logger.info("OCR 텍스트 검증 모드 - 완화된 기준 적용")
                
                # OCR 텍스트를 위한 완화된 키워드
                ocr_keywords = [
                    '채용', '모집', '지원', '인턴', '신입', '경력',
                    '업무', '담당', '개발', '마케팅', '영업', '관리',
                    '자격', '우대', '조건', '요구사항', '혜택', '복리후생',
                    'recruit', 'hiring', 'job', 'position', 'intern',
                    'development', 'manager', 'engineer', 'designer'
                ]
                
                # OCR 텍스트에서 키워드 확인
                found_keywords = sum(1 for keyword in ocr_keywords if keyword in text_lower)
                keyword_score = min(found_keywords / 10, 1.0)  # 10개 중 찾은 비율
                
                # 텍스트 길이 점수 (OCR은 더 관대하게)
                length_score = min(len(text) / 1000, 1.0)  # 1000자 기준
                
                # 구조 점수 (OCR은 간단하게)
                structure_indicators = [':', '·', '-', '※', '○', '□', '■']
                structure_score = min(sum(1 for indicator in structure_indicators if indicator in text) / 3, 1.0)
                
                # OCR 텍스트 종합 점수 (키워드 중심)
                final_score = (keyword_score * 0.6) + (length_score * 0.3) + (structure_score * 0.1)
                
                # OCR 텍스트는 기준을 더 완화 (0.15 -> 0.1)
                is_valid = final_score >= 0.1 or found_keywords >= 2
                
                if is_valid:
                    status = f"OCR 텍스트 검증 통과 (키워드: {found_keywords}개)"
                else:
                    status = f"OCR 텍스트 검증 실패 (키워드: {found_keywords}개, 점수: {final_score:.2f})"
                
                logger.info(f"OCR 텍스트 검증: 키워드 {found_keywords}개, 점수 {final_score:.2f}, 결과 {'통과' if is_valid else '실패'}")
                return is_valid, final_score, status
            
            # 일반 텍스트 검증 (기존 로직)
            else:
                # 1. 필수 키워드 확인
                essential_keywords = [
                    '채용', '모집', '지원', '인턴', '신입', '경력', '업무', '담당', '개발', '마케팅', '영업',
                    'recruit', 'hiring', 'job', 'position', 'intern', 'development', 'manager'
                ]
                
                found_essential = sum(1 for kw in essential_keywords if kw.lower() in text_lower)
                keyword_score = min(found_essential / 5, 1.0)
                
                # 2. 텍스트 길이 평가
                length_score = min(len(text) / 2000, 1.0)
                
                # 3. 구조적 요소 확인
                structure_keywords = ['자격요건', '우대사항', '담당업무', '혜택', '복리후생', '근무조건', '지원방법']
                has_structure = any(keyword in text_lower for keyword in structure_keywords)
                structure_score = 1.0 if has_structure else 0.3
                
                # 종합 점수 계산
                final_score = (keyword_score * 0.4) + (length_score * 0.3) + (structure_score * 0.3)
                
                # 검증 조건 (완화됨)
                is_valid = final_score >= 0.15 or found_essential >= 2
                
                if is_valid:
                    status = "채용공고 검증 통과"
                elif found_essential < 1:
                    status = "필수 키워드 부족"
                elif final_score < 0.15:
                    status = "내용이 너무 간단합니다"
                else:
                    status = f"검증 실패 (점수: {final_score:.2f})"
                
                return is_valid, final_score, status
            
        except Exception as e:
            logger.error(f"채용공고 검증 중 오류: {e}")
            return False, 0.0, "검증 중 오류 발생"