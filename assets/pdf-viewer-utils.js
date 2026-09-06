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

export function clampedRenderPixelRatio(cssWidth, cssHeight, devicePixelRatio = 1, maxRatio = 2, maxPixels = 4_000_000) {
  const width = Number(cssWidth);
  const height = Number(cssHeight);
  if (![width, height].every((value) => Number.isFinite(value) && value > 0)) return 1;
  const requested = Math.max(1, Math.min(Number(devicePixelRatio) || 1, maxRatio));
  const memoryLimit = Math.sqrt(maxPixels / (width * height));
  return Math.max(1, Math.min(requested, memoryLimit));
}
