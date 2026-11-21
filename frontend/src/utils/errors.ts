/**
 * Format any API error or exception into a clean, safe, human-readable string.
 * Prevents React child rendering errors when backend (FastAPI / Pydantic) returns
 * structured validation errors like [{type, loc, msg, input}].
 */
export const formatApiError = (
  error: any,
  fallbackMessage: string = 'An unexpected error occurred. Please try again.'
): string => {
  if (!error) return fallbackMessage;

  // 1. Direct string error
  if (typeof error === 'string') return error;

  // 2. Axios response error with detail
  const detail = error?.response?.data?.detail ?? error?.detail ?? error?.message;

  if (typeof detail === 'string') {
    return detail.trim() || fallbackMessage;
  }

  // 3. FastAPI / Pydantic validation error array: [{type, loc, msg, input}]
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item: any) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const locArr = Array.isArray(item.loc) ? item.loc.filter((x: any) => x !== 'body') : [];
          const field = locArr.join('.');
          const msg = item.msg || item.message || JSON.stringify(item);
          return field ? `${field}: ${msg}` : msg;
        }
        return String(item);
      })
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join('; ');
    }
  }

  // 4. Object error
  if (typeof detail === 'object' && detail !== null) {
    if (detail.msg) return String(detail.msg);
    if (detail.message) return String(detail.message);
    try {
      return JSON.stringify(detail);
    } catch {
      return fallbackMessage;
    }
  }

  // 5. Fallback
  return error?.message || fallbackMessage;
};
