/**
 * Device metadata utilities
 * Captures device information for verification tracking
 */

export const getDeviceInfo = (): string => {
  const ua = navigator.userAgent;

  // Detect device type
  const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(ua);
  const isTablet = /iPad|Android(?!.*Mobile)/i.test(ua);
  const isDesktop = !isMobile && !isTablet;

  // Detect OS
  let os = 'Unknown';
  if (/Windows/i.test(ua)) os = 'Windows';
  else if (/Mac OS X/i.test(ua)) os = 'macOS';
  else if (/Linux/i.test(ua)) os = 'Linux';
  else if (/Android/i.test(ua)) os = 'Android';
  else if (/iPhone|iPad|iPod/i.test(ua)) os = 'iOS';

  // Detect browser
  let browser = 'Unknown';
  if (/Firefox/i.test(ua)) browser = 'Firefox';
  else if (/Chrome/i.test(ua) && !/Edg/i.test(ua)) browser = 'Chrome';
  else if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) browser = 'Safari';
  else if (/Edg/i.test(ua)) browser = 'Edge';

  // Build device string
  const deviceType = isDesktop ? 'Desktop' : isTablet ? 'Tablet' : 'Mobile';
  return `${deviceType} (${os}, ${browser})`;
};

export const getUserAgent = (): string => {
  return navigator.userAgent;
};
