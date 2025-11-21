const STORAGE_KEY = 'graintrade_cookie_consent_v1';

function isBrowser() {
    return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

export function loadConsent() {
    if (!isBrowser()) {
        return null;
    }
    try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        if (!raw) {
            return null;
        }
        return JSON.parse(raw);
    } catch (error) {
        console.warn('Failed to parse stored cookie consent:', error);
        return null;
    }
}

export function saveConsent(consent) {
    if (!isBrowser()) {
        return;
    }
    try {
        const payload = {
            necessary: true,
            analytics: Boolean(consent?.analytics),
            updatedAt: new Date().toISOString(),
        };
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (error) {
        console.warn('Failed to persist cookie consent:', error);
    }
}

export function clearConsent() {
    if (!isBrowser()) {
        return;
    }
    window.localStorage.removeItem(STORAGE_KEY);
}

export function hasAnalyticsConsent(consent) {
    return Boolean(consent && consent.analytics === true);
}

export function getConsentStatus(consent) {
    if (!consent) {
        return 'pending';
    }
    return consent.analytics ? 'granted' : 'denied';
}
