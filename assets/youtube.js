const VIDEO_ID_PATTERN = /^[A-Za-z0-9_-]{11}$/;
const YOUTUBE_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
  "youtube-nocookie.com",
  "www.youtube-nocookie.com"
]);

export function isValidYouTubeVideoId(value) {
  return typeof value === "string" && VIDEO_ID_PATTERN.test(value);
}

export function extractYouTubeVideoId(value) {
  if (typeof value !== "string") return null;
  const input = value.trim();
  if (!input || /[<>]/.test(input)) return null;
  if (isValidYouTubeVideoId(input)) return input;

  let url;
  try {
    url = new URL(input);
  } catch {
    return null;
  }

  if (url.protocol !== "https:" && url.protocol !== "http:") return null;

  const host = url.hostname.toLowerCase();
  let candidate = null;

  if (host === "youtu.be" || host === "www.youtu.be") {
    candidate = url.pathname.split("/").filter(Boolean)[0] || null;
  } else if (YOUTUBE_HOSTS.has(host)) {
    const segments = url.pathname.split("/").filter(Boolean);
    if (url.pathname === "/watch") {
      candidate = url.searchParams.get("v");
    } else if (["embed", "shorts", "live"].includes(segments[0])) {
      candidate = segments[1] || null;
    }
  }

  return isValidYouTubeVideoId(candidate) ? candidate : null;
}

export function normalizeYouTubeUrl(value) {
  const videoId = extractYouTubeVideoId(value);
  return videoId ? `https://www.youtube.com/watch?v=${videoId}` : null;
}

export function youtubeThumbnailUrl(videoId) {
  if (!isValidYouTubeVideoId(videoId)) return null;
  return `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
}

export function youtubeWatchUrl(videoId) {
  if (!isValidYouTubeVideoId(videoId)) return null;
  return `https://www.youtube.com/watch?v=${videoId}`;
}
