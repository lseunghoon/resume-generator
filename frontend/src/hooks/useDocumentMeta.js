import { useEffect } from 'react';

/**
 * React 19 네이티브 방식으로 document head를 관리하는 커스텀 hook
 * 외부 라이브러리 의존성 없이 SEO 메타데이터를 안전하게 설정
 */
export const useDocumentMeta = ({ 
  title, 
  description, 
  keywords,
  robots = 'index, follow',
  ogTitle,
  ogDescription,
  ogType = 'website',
  ogUrl,
  ogImage,
  ogImageWidth,
  ogImageHeight,
  ogSiteName,
  ogLocale,
  twitterCard = 'summary_large_image',
  twitterTitle,
  twitterDescription,
  twitterImage,
  jsonLd
}) => {
  useEffect(() => {
    // 기존 동적으로 추가된 메타 태그들 정리
    const existingMetas = document.querySelectorAll('meta[data-dynamic="true"]');
    existingMetas.forEach(meta => meta.remove());

    const existingJsonLd = document.querySelectorAll('script[type="application/ld+json"][data-dynamic="true"]');
    existingJsonLd.forEach(script => script.remove());

    // Title 설정
    if (title) {
      document.title = title;
    }

    // Meta 태그들 생성 및 추가
    const metaTags = [];

    if (description) {
      metaTags.push({ name: 'description', content: description });
    }

    if (keywords) {
      metaTags.push({ name: 'keywords', content: keywords });
    }

    if (robots) {
      metaTags.push({ name: 'robots', content: robots });
    }

    // Open Graph 태그들
    if (ogTitle) {
      metaTags.push({ property: 'og:title', content: ogTitle });
    }

    if (ogDescription) {
      metaTags.push({ property: 'og:description', content: ogDescription });
    }

    if (ogType) {
      metaTags.push({ property: 'og:type', content: ogType });
    }

    if (ogUrl) {
      metaTags.push({ property: 'og:url', content: ogUrl });
    }

    if (ogImage) {
      metaTags.push({ property: 'og:image', content: ogImage });
    }

    if (ogImageWidth) {
      metaTags.push({ property: 'og:image:width', content: ogImageWidth });
    }

    if (ogImageHeight) {
      metaTags.push({ property: 'og:image:height', content: ogImageHeight });
    }

    if (ogSiteName) {
      metaTags.push({ property: 'og:site_name', content: ogSiteName });
    }

    if (ogLocale) {
      metaTags.push({ property: 'og:locale', content: ogLocale });
    }

    // Twitter 카드 태그들
    if (twitterCard) {
      metaTags.push({ name: 'twitter:card', content: twitterCard });
    }

    if (twitterTitle) {
      metaTags.push({ name: 'twitter:title', content: twitterTitle });
    }

    if (twitterDescription) {
      metaTags.push({ name: 'twitter:description', content: twitterDescription });
    }

    if (twitterImage) {
      metaTags.push({ name: 'twitter:image', content: twitterImage });
    }

    // 메타 태그들을 DOM에 추가
    metaTags.forEach(({ name, property, content }) => {
      const meta = document.createElement('meta');
      if (name) meta.setAttribute('name', name);
      if (property) meta.setAttribute('property', property);
      meta.setAttribute('content', content);
      meta.setAttribute('data-dynamic', 'true'); // 정리용 마커
      document.head.appendChild(meta);
    });

    // JSON-LD 구조화된 데이터 추가
    if (jsonLd) {
      const script = document.createElement('script');
      script.type = 'application/ld+json';
      script.setAttribute('data-dynamic', 'true'); // 정리용 마커
      script.textContent = JSON.stringify(jsonLd);
      document.head.appendChild(script);
    }

    // Cleanup function - 컴포넌트 언마운트 시 정리
    return () => {
      const dynamicMetas = document.querySelectorAll('meta[data-dynamic="true"]');
      dynamicMetas.forEach(meta => meta.remove());

      const dynamicJsonLd = document.querySelectorAll('script[type="application/ld+json"][data-dynamic="true"]');
      dynamicJsonLd.forEach(script => script.remove());
    };
  }, [
    title, description, keywords, robots,
    ogTitle, ogDescription, ogType, ogUrl, ogImage, ogImageWidth, ogImageHeight, ogSiteName, ogLocale,
    twitterCard, twitterTitle, twitterDescription, twitterImage,
    jsonLd
  ]);
};

export default useDocumentMeta;
