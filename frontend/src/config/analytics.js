const isProduction = process.env.NODE_ENV === 'production';
let analyticsInitialized = false;
let currentGaMeasurementId = null;
let clarityProjectIdCache = null;

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
    if (analyticsInitialized) {
        return;
    }
    if (!isProduction) {
        return;
    }
    if (typeof window === 'undefined' || typeof document === 'undefined') {
        return;
    }

    const gaMeasurementId = process.env.VUE_APP_GA4_MEASUREMENT_ID;
    const clarityProjectId = process.env.VUE_APP_MS_CLARITY_PROJECT_ID;

    if (gaMeasurementId) {
        window[`ga-disable-${gaMeasurementId}`] = false;
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
        clarityProjectIdCache = clarityProjectId;
    }

    analyticsInitialized = Boolean(gaMeasurementId || clarityProjectId);
    currentGaMeasurementId = gaMeasurementId || null;
}

export function disableAnalytics() {
    if (!analyticsInitialized) {
        return;
    }
    if (typeof window === 'undefined' || typeof document === 'undefined') {
        return;
    }

    if (currentGaMeasurementId) {
        window[`ga-disable-${currentGaMeasurementId}`] = true;
    }

    const gtagScript = document.querySelector(
        'script[src^="https://www.googletagmanager.com/gtag/js"]'
    );
    if (gtagScript && gtagScript.parentNode) {
        gtagScript.parentNode.removeChild(gtagScript);
    }

    const gaInline = document.getElementById('ga4-init');
    if (gaInline && gaInline.parentNode) {
        gaInline.parentNode.removeChild(gaInline);
    }

    if (clarityProjectIdCache) {
        const clarityScript = document.querySelector(
            'script[src^="https://www.clarity.ms/tag/"]'
        );
        if (clarityScript && clarityScript.parentNode) {
            clarityScript.parentNode.removeChild(clarityScript);
        }
        const clarityInline = document.getElementById('ms-clarity-init');
        if (clarityInline && clarityInline.parentNode) {
            clarityInline.parentNode.removeChild(clarityInline);
        }
        try {
            if (typeof window.clarity === 'function') {
                window.clarity('stop');
            }
        } catch (error) {
            /* swallow */
        }
        delete window.clarity;
    }

    analyticsInitialized = false;
    currentGaMeasurementId = null;
    clarityProjectIdCache = null;
}
