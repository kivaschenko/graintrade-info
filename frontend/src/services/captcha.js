const CAPTCHA_ENABLED = String(process.env.VUE_APP_CAPTCHA_ENABLED || '').toLowerCase() === 'true';
const CAPTCHA_SITE_KEY = process.env.VUE_APP_CAPTCHA_SITE_KEY || '';

let scriptLoadPromise = null;

function waitForGrecaptchaReady(resolve, reject) {
  const startedAt = Date.now();
  const maxWaitMs = 5000;

  const check = () => {
    if (window.grecaptcha && typeof window.grecaptcha.ready === 'function') {
      resolve(window.grecaptcha);
      return;
    }

    if (Date.now() - startedAt > maxWaitMs) {
      scriptLoadPromise = null;
      reject(new Error('CAPTCHA is not available'));
      return;
    }

    window.setTimeout(check, 50);
  };

  check();
}

function loadRecaptchaScript() {
  if (scriptLoadPromise) {
    return scriptLoadPromise;
  }

  scriptLoadPromise = new Promise((resolve, reject) => {
    if (window.grecaptcha && typeof window.grecaptcha.ready === 'function') {
      resolve(window.grecaptcha);
      return;
    }

    const script = document.createElement('script');
    script.src = `https://www.google.com/recaptcha/api.js?render=${encodeURIComponent(CAPTCHA_SITE_KEY)}`;
    script.async = true;
    script.defer = true;
    script.onload = () => waitForGrecaptchaReady(resolve, reject);
    script.onerror = () => {
      scriptLoadPromise = null;
      reject(new Error('Failed to load CAPTCHA script'));
    };
    document.head.appendChild(script);
  });

  return scriptLoadPromise;
}

export async function getCaptchaToken(action) {
  if (!CAPTCHA_ENABLED) {
    return null;
  }

  if (!CAPTCHA_SITE_KEY) {
    throw new Error('CAPTCHA site key is not configured');
  }

  const grecaptcha = await loadRecaptchaScript();
  if (!grecaptcha || typeof grecaptcha.ready !== 'function' || typeof grecaptcha.execute !== 'function') {
    throw new Error('CAPTCHA is not available');
  }

  await new Promise((resolve) => grecaptcha.ready(resolve));
  return grecaptcha.execute(CAPTCHA_SITE_KEY, { action });
}
