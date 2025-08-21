const { SitemapStream, streamToPromise } = require('sitemap');
const { createWriteStream } = require('fs');
const { resolve } = require('path');

// sseojum의 모든 라우트 정의
const routes = [
  { url: '/', changefreq: 'daily', priority: 1.0 },
  { url: '/file-upload', changefreq: 'monthly', priority: 0.8 },
  { url: '/job-info', changefreq: 'monthly', priority: 0.8 },
  { url: '/question', changefreq: 'monthly', priority: 0.8 },
  { url: '/result', changefreq: 'monthly', priority: 0.7 },
  { url: '/privacy', changefreq: 'yearly', priority: 0.3 },
  { url: '/login', changefreq: 'yearly', priority: 0.5 }
];

async function generateSitemap() {
  const sitemap = new SitemapStream({ 
    hostname: 'https://www.sseojum.com',
    xmlns: {
      news: false,
      xhtml: false,
      image: false,
      video: false
    }
  });

  routes.forEach(route => {
    sitemap.write(route);
  });

  sitemap.end();

  const sitemapXML = await streamToPromise(sitemap);
  
  // XML을 보기 좋게 포맷팅
  const formattedXML = formatXML(sitemapXML.toString());
  
  // public 폴더에 sitemap.xml 생성
  const writeStream = createWriteStream(resolve(__dirname, '../public/sitemap.xml'));
  writeStream.write(formattedXML);
  writeStream.end();
  
  console.log('Sitemap generated successfully!');
}

// XML 포맷팅 함수
function formatXML(xml) {
  const formatted = xml
    .replace(/></g, '>\n<')
    .replace(/<\?xml/g, '<?xml')
    .replace(/<urlset/g, '\n<urlset')
    .replace(/<\/urlset>/g, '\n</urlset>')
    .replace(/<url>/g, '\n  <url>')
    .replace(/<\/url>/g, '\n  </url>')
    .replace(/<loc>/g, '\n    <loc>')
    .replace(/<\/loc>/g, '</loc>')
    .replace(/<changefreq>/g, '\n    <changefreq>')
    .replace(/<\/changefreq>/g, '</changefreq>')
    .replace(/<priority>/g, '\n    <priority>')
    .replace(/<\/priority>/g, '</priority>');
  
  return formatted;
}

generateSitemap().catch(console.error);