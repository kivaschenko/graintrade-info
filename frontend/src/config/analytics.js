const isProduction = process.env.NODE_ENV === 'production';

function injectScript(src, attributes = {}) {
    if (!src || document.querySelector(`script[src="${src}"]`)) {
        return;
    }
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    Object.entries(attributes).forEach(([key, value]) => {
        script.setAttribute(key, value);
    });
    document.head.appendChild(script);
}

function injectInlineScript(id, content) {
    if (!content || document.getElementById(id)) {
        return;
    }
    const script = document.createElement('script');
    script.id = id;
    script.text = content;
    document.head.appendChild(script);
}

export function initAnalytics() {
    if (!isProduction) {
        return;
    }

    const gaMeasurementId = process.env.VUE_APP_GA4_MEASUREMENT_ID;
    const clarityProjectId = process.env.VUE_APP_MS_CLARITY_PROJECT_ID;

    if (gaMeasurementId) {
        injectScript(`https://www.googletagmanager.com/gtag/js?id=${gaMeasurementId}`);
        injectInlineScript(
            'ga4-init',
            `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '${gaMeasurementId}', {
  send_page_view: true,
  anonymize_ip: true
});`
        );
    }

    if (clarityProjectId) {
        injectInlineScript(
            'ms-clarity-init',
            `(function(c,l,a,r,i,t,y){
  c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
  t=l.createElement(r);
  t.async=1;
  t.src="https://www.clarity.ms/tag/"+i;
  y=l.getElementsByTagName(r)[0];
  y.parentNode.insertBefore(t,y);
})(window, document, 'clarity', 'script', '${clarityProjectId}');`
        );
    }
}
