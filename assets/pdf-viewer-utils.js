export function fitPageScale(containerWidth, containerHeight, pageWidth, pageHeight) {
  const values = [containerWidth, containerHeight, pageWidth, pageHeight].map(Number);
  if (values.some((value) => !Number.isFinite(value) || value <= 0)) return 0;
  return Math.min(values[0] / values[2], values[1] / values[3]);
}

export function fitPageDimensions(containerWidth, containerHeight, pageWidth, pageHeight) {
  const scale = fitPageScale(containerWidth, containerHeight, pageWidth, pageHeight);
  return scale > 0
    ? {
        scale,
        width: Math.min(Number(containerWidth), Number(pageWidth) * scale),
        height: Math.min(Number(containerHeight), Number(pageHeight) * scale)
      }
    : { scale: 0, width: 0, height: 0 };
}

export function fitWidthScale(containerWidth, pageWidth) {
  const values = [containerWidth, pageWidth].map(Number);
  if (values.some((value) => !Number.isFinite(value) || value <= 0)) return 0;
  return values[0] / values[1];
}

export function clampPageNumber(value, numPages) {
  const total = Math.max(1, Math.trunc(Number(numPages) || 1));
  const requested = Math.trunc(Number(value));
  if (!Number.isFinite(requested)) return 1;
  return Math.min(total, Math.max(1, requested));
}

export function clampZoom(value, minimum = 0.25, maximum = 3) {
  const zoom = Number(value);
  if (!Number.isFinite(zoom)) return minimum;
  return Math.min(maximum, Math.max(minimum, zoom));
}

export function stepZoom(value, direction, step = 0.1, minimum = 0.25, maximum = 3) {
  const delta = Math.sign(Number(direction)) * Number(step);
  if (!Number.isFinite(delta)) return clampZoom(value, minimum, maximum);
  return clampZoom(Math.round((Number(value) + delta) * 1000) / 1000, minimum, maximum);
}

export function zoomPercentage(scale) {
  const value = Number(scale);
  return Number.isFinite(value) && value > 0 ? Math.round(value * 100) : 0;
}

export function normalizeRotation(rotation) {
  const value = Number(rotation);
  if (!Number.isFinite(value)) return 0;
  return ((Math.round(value / 90) * 90) % 360 + 360) % 360;
}

export function rotatedPageDimensions(width, height, rotation) {
  const values = [width, height].map(Number);
  if (values.some((value) => !Number.isFinite(value) || value <= 0)) return { width: 0, height: 0 };
  return normalizeRotation(rotation) % 180 === 0
    ? { width: values[0], height: values[1] }
    : { width: values[1], height: values[0] };
}

export function scaleForViewMode(mode, availableWidth, availableHeight, pageWidth, pageHeight, customZoom = 1) {
  if (mode === "fit-page") return fitPageScale(availableWidth, availableHeight, pageWidth, pageHeight);
  if (mode === "fit-width") return fitWidthScale(availableWidth, pageWidth);
  if (mode === "custom") return clampZoom(customZoom);
  return 0;
}

export function clampedRenderPixelRatio(cssWidth, cssHeight, devicePixelRatio = 1, maxRatio = 2, maxPixels = 4_000_000) {
  const width = Number(cssWidth);
  const height = Number(cssHeight);
  if (![width, height].every((value) => Number.isFinite(value) && value > 0)) return 1;
  const requested = Math.max(1, Math.min(Number(devicePixelRatio) || 1, maxRatio));
  const memoryLimit = Math.sqrt(maxPixels / (width * height));
  return Math.max(1, Math.min(requested, memoryLimit));
}
