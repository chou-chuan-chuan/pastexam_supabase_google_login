import { isValidYouTubeVideoId, youtubeWatchUrl } from "./youtube.js";

let apiPromise;

export function loadYouTubeIframeAPI(browserWindow = window) {
  if (browserWindow.YT?.Player) return Promise.resolve(browserWindow.YT);
  if (apiPromise) return apiPromise;

  apiPromise = new Promise((resolve, reject) => {
    const previous = browserWindow.onYouTubeIframeAPIReady;
    browserWindow.onYouTubeIframeAPIReady = () => {
      if (typeof previous === "function") previous();
      resolve(browserWindow.YT);
    };

    const existing = browserWindow.document.querySelector('script[src="https://www.youtube.com/iframe_api"]');
    if (existing) return;

    const script = browserWindow.document.createElement("script");
    script.src = "https://www.youtube.com/iframe_api";
    script.async = true;
    script.onerror = () => reject(new Error("無法載入 YouTube 播放器 API。"));
    browserWindow.document.head.append(script);
  });

  return apiPromise;
}

export class YouTubePlayer {
  constructor(container, videoId, handlers = {}) {
    if (!container) throw new TypeError("YouTube player container is required.");
    if (!isValidYouTubeVideoId(videoId)) throw new TypeError("Invalid YouTube video ID.");
    this.container = container;
    this.videoId = videoId;
    this.handlers = handlers;
    this.player = null;
    this.ready = false;
  }

  async create() {
    if (this.player) return this;
    const YT = await loadYouTubeIframeAPI();
    this.player = new YT.Player(this.container, {
      videoId: this.videoId,
      playerVars: {
        autoplay: 0,
        controls: 1,
        playsinline: 1,
        rel: 0,
        origin: window.location.origin
      },
      events: {
        onReady: (event) => {
          this.ready = true;
          this.handlers.onReady?.(event);
        },
        onStateChange: (event) => this.handlers.onStateChange?.(event.data, event),
        onError: (event) => this.handlers.onError?.(event.data, youtubeWatchUrl(this.videoId))
      }
    });
    return this;
  }

  getCurrentTimeMs() {
    if (!this.ready || !this.player?.getCurrentTime) return 0;
    return Math.round(this.player.getCurrentTime() * 1_000);
  }

  seekTo(milliseconds) {
    if (this.ready) this.player.seekTo(Math.max(0, milliseconds) / 1_000, true);
  }

  play() {
    if (this.ready) this.player.playVideo();
  }

  pause() {
    if (this.ready) this.player.pauseVideo();
  }

  destroy() {
    this.player?.destroy?.();
    this.player = null;
    this.ready = false;
  }
}
