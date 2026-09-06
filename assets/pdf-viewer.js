import { clampedRenderPixelRatio, fitPageDimensions } from "./pdf-viewer-utils.js";

export const PDFJS_VERSION = "4.10.38";
export const PDFJS_MODULE_URL = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${PDFJS_VERSION}/build/pdf.min.mjs`;
export const PDFJS_WORKER_URL = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${PDFJS_VERSION}/build/pdf.worker.min.mjs`;

let pdfJsPromise;

async function loadPdfJs() {
  if (!pdfJsPromise) {
    pdfJsPromise = import(PDFJS_MODULE_URL).then((pdfjs) => {
      if (pdfjs.version !== PDFJS_VERSION) throw new Error("PDF.js 版本不一致。");
      pdfjs.GlobalWorkerOptions.workerSrc = PDFJS_WORKER_URL;
      return pdfjs;
    });
  }
  return pdfJsPromise;
}

function element(tag, className, text) {
  const item = document.createElement(tag);
  item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}

function cancelled(error) {
  return error?.name === "AbortError" || error?.name === "RenderingCancelledException";
}

export class PdfViewer {
  constructor(host, { label = "PDF 文件閱讀器" } = {}) {
    if (!(host instanceof HTMLElement)) throw new TypeError("PdfViewer 需要有效的容器。");
    this.host = host;
    this.host.classList.add("pdf-viewer");
    this.status = element("div", "pdf-viewer-status", "尚未載入 PDF");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    this.scroll = element("div", "pdf-viewer-scroll");
    this.scroll.tabIndex = 0;
    this.scroll.setAttribute("role", "document");
    this.scroll.setAttribute("aria-label", label);
    this.pagesHost = element("div", "pdf-viewer-pages");
    this.scroll.append(this.pagesHost);
    this.host.replaceChildren(this.status, this.scroll);

    this.pages = [];
    this.pdfDocument = null;
    this.loadingTask = null;
    this.abortController = null;
    this.intersectionObserver = null;
    this.resizeObserver = null;
    this.resizeTimer = 0;
    this.pendingResizePosition = null;
    this.lastStablePosition = null;
    this.scrollFrame = 0;
    this.generation = 0;
    this.lastSize = { width: 0, height: 0 };
    this.onScroll = () => {
      this.lastStablePosition = this.capturePosition();
      this.schedulePageStatusUpdate();
    };
    this.scroll.addEventListener("scroll", this.onScroll, { passive: true });
  }

  setStatus(text, kind = "") {
    this.status.textContent = text;
    this.status.className = `pdf-viewer-status${kind ? ` is-${kind}` : ""}`;
  }

  availableSize() {
    const style = getComputedStyle(this.scroll);
    const horizontalPadding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
    const verticalPadding = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
    return {
      width: Math.max(1, this.scroll.clientWidth - horizontalPadding),
      height: Math.max(1, this.scroll.clientHeight - verticalPadding)
    };
  }

  async load(url) {
    await this.destroy();
    const generation = ++this.generation;
    this.host.classList.add("is-loading");
    this.setStatus("正在載入 PDF…", "loading");
    this.abortController = new AbortController();

    try {
      const [pdfjs, response] = await Promise.all([
        loadPdfJs(),
        fetch(url, {
          signal: this.abortController.signal,
          cache: "no-store",
          credentials: "omit",
          referrerPolicy: "no-referrer"
        })
      ]);
      if (!response.ok) throw new Error(`PDF 下載失敗（${response.status}）。`);
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (generation !== this.generation) return false;

      this.loadingTask = pdfjs.getDocument({ data: bytes });
      const pdfDocument = await this.loadingTask.promise;
      if (generation !== this.generation) {
        await pdfDocument.destroy();
        return false;
      }
      this.loadingTask = null;
      this.pdfDocument = pdfDocument;
      await new Promise((resolve) => requestAnimationFrame(resolve));
      await this.createPagePlaceholders(generation);
      if (generation !== this.generation) return false;
      this.observePages(generation);
      this.observeResize(generation);
      this.host.classList.remove("is-loading");
      this.setStatus(`1 / ${pdfDocument.numPages}`);
      await this.renderPage(this.pages[0], generation);
      return true;
    } catch (error) {
      if (generation !== this.generation || cancelled(error)) return false;
      this.host.classList.remove("is-loading");
      this.host.classList.add("has-error");
      this.setStatus("PDF 載入失敗，請使用另開或下載。", "error");
      throw error;
    }
  }

  async createPagePlaceholders(generation) {
    const pageStates = [];
    for (let pageNumber = 1; pageNumber <= this.pdfDocument.numPages; pageNumber += 1) {
      const page = await this.pdfDocument.getPage(pageNumber);
      if (generation !== this.generation) return;
      const baseViewport = page.getViewport({ scale: 1 });
      const pageElement = element("section", "pdf-page is-pending");
      pageElement.dataset.pageNumber = String(pageNumber);
      pageElement.setAttribute("role", "group");
      pageElement.setAttribute("aria-label", `PDF 第 ${pageNumber} 頁，共 ${this.pdfDocument.numPages} 頁`);
      pageElement.append(element("span", "pdf-page-loading", `第 ${pageNumber} 頁`));
      this.pagesHost.append(pageElement);
      pageStates.push({
        number: pageNumber,
        page,
        baseViewport,
        element: pageElement,
        scale: 0,
        width: 0,
        height: 0,
        renderTask: null,
        rendered: false
      });
    }
    this.pages = pageStates;
    this.layoutPages(false);
    this.lastStablePosition = this.capturePosition();
  }

  capturePosition() {
    if (!this.pages.length) return null;
    const scrollTop = this.scroll.scrollTop;
    let current = this.pages[0];
    const center = scrollTop + this.scroll.clientHeight / 2;
    let distance = Infinity;
    for (const page of this.pages) {
      const nextDistance = Math.abs(this.pageScrollOffset(page) + page.height / 2 - center);
      if (nextDistance < distance) {
        current = page;
        distance = nextDistance;
      }
    }
    return {
      number: current.number,
      ratio: (center - this.pageScrollOffset(current)) / Math.max(1, current.height),
      atEnd: this.scroll.scrollHeight - this.scroll.clientHeight - scrollTop < 2
    };
  }

  pageScrollOffset(page) {
    return page.element.getBoundingClientRect().top - this.scroll.getBoundingClientRect().top + this.scroll.scrollTop;
  }

  layoutPages(preservePosition = true, positionOverride = null) {
    if (!this.pages.length) return;
    const position = positionOverride || (preservePosition ? this.capturePosition() : null);
    const available = this.availableSize();
    this.lastSize = available;

    for (const page of this.pages) {
      const fitted = fitPageDimensions(available.width, available.height, page.baseViewport.width, page.baseViewport.height);
      const changed = Math.abs(page.width - fitted.width) > 0.5 || Math.abs(page.height - fitted.height) > 0.5;
      page.scale = fitted.scale;
      page.width = fitted.width;
      page.height = fitted.height;
      page.element.style.width = `${fitted.width}px`;
      page.element.style.height = `${fitted.height}px`;
      if (changed && (page.rendered || page.renderTask)) this.resetRenderedPage(page);
    }

    if (position) {
      const anchor = this.pages[position.number - 1];
      this.scroll.scrollTop = position.atEnd
        ? this.scroll.scrollHeight
        : Math.max(0, this.pageScrollOffset(anchor) + position.ratio * anchor.height - this.scroll.clientHeight / 2);
    }
  }

  resetRenderedPage(page) {
    page.renderTask?.cancel();
    page.renderTask = null;
    page.rendered = false;
    page.element.className = "pdf-page is-pending";
    page.element.replaceChildren(element("span", "pdf-page-loading", `第 ${page.number} 頁`));
  }

  observePages(generation) {
    if (!("IntersectionObserver" in window)) {
      for (const page of this.pages) void this.renderPage(page, generation);
      return;
    }
    this.intersectionObserver = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          const page = this.pages[Number(entry.target.dataset.pageNumber) - 1];
          void this.renderPage(page, generation);
        }
      }
    }, { root: this.scroll, rootMargin: `${Math.max(200, this.scroll.clientHeight)}px 0px`, threshold: 0.01 });
    for (const page of this.pages) this.intersectionObserver.observe(page.element);
  }

  observeResize(generation) {
    this.resizeObserver = new ResizeObserver(() => {
      if (!this.pendingResizePosition) this.pendingResizePosition = this.lastStablePosition || this.capturePosition();
      clearTimeout(this.resizeTimer);
      this.resizeTimer = setTimeout(() => {
        const position = this.pendingResizePosition;
        this.pendingResizePosition = null;
        if (generation !== this.generation || !this.pages.length) return;
        const nextSize = this.availableSize();
        if (Math.abs(nextSize.width - this.lastSize.width) < 1 && Math.abs(nextSize.height - this.lastSize.height) < 1) return;
        for (const page of this.pages) page.renderTask?.cancel();
        this.layoutPages(false, position);
        this.lastStablePosition = this.capturePosition();
        this.renderNearbyPages(generation);
        this.updatePageStatus();
      }, 120);
    });
    this.resizeObserver.observe(this.scroll);
  }

  renderNearbyPages(generation) {
    const rootRect = this.scroll.getBoundingClientRect();
    for (const page of this.pages) {
      const rect = page.element.getBoundingClientRect();
      if (rect.bottom >= rootRect.top - rootRect.height && rect.top <= rootRect.bottom + rootRect.height) {
        void this.renderPage(page, generation);
      }
    }
  }

  async renderPage(page, generation) {
    if (!page || page.rendered || page.renderTask || generation !== this.generation || page.scale <= 0) return;
    const viewport = page.page.getViewport({ scale: page.scale });
    const pixelRatio = clampedRenderPixelRatio(viewport.width, viewport.height, window.devicePixelRatio);
    const canvas = document.createElement("canvas");
    canvas.className = "pdf-page-canvas";
    canvas.setAttribute("aria-hidden", "true");
    canvas.width = Math.max(1, Math.floor(viewport.width * pixelRatio));
    canvas.height = Math.max(1, Math.floor(viewport.height * pixelRatio));
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;
    const context = canvas.getContext("2d", { alpha: false });
    if (!context) throw new Error("瀏覽器無法建立 PDF canvas。");
    page.element.className = "pdf-page is-rendering";
    page.element.replaceChildren(canvas);
    const renderTask = page.page.render({
      canvasContext: context,
      viewport,
      transform: pixelRatio === 1 ? null : [pixelRatio, 0, 0, pixelRatio, 0, 0]
    });
    page.renderTask = renderTask;
    try {
      await renderTask.promise;
      if (generation !== this.generation) return;
      page.rendered = true;
      page.element.className = "pdf-page is-rendered";
    } catch (error) {
      if (!cancelled(error) && generation === this.generation) {
        page.element.className = "pdf-page has-error";
        page.element.replaceChildren(element("span", "pdf-page-error", `第 ${page.number} 頁無法顯示`));
      }
    } finally {
      if (page.renderTask === renderTask) page.renderTask = null;
    }
  }

  schedulePageStatusUpdate() {
    cancelAnimationFrame(this.scrollFrame);
    this.scrollFrame = requestAnimationFrame(() => this.updatePageStatus());
  }

  updatePageStatus() {
    if (!this.pages.length) return;
    const center = this.scroll.scrollTop + this.scroll.clientHeight / 2;
    let current = this.pages[0];
    let distance = Infinity;
    for (const page of this.pages) {
      const pageCenter = this.pageScrollOffset(page) + page.height / 2;
      const nextDistance = Math.abs(pageCenter - center);
      if (nextDistance < distance) {
        current = page;
        distance = nextDistance;
      }
    }
    this.setStatus(`${current.number} / ${this.pages.length}`);
  }

  async destroy() {
    ++this.generation;
    this.abortController?.abort();
    this.abortController = null;
    this.intersectionObserver?.disconnect();
    this.intersectionObserver = null;
    this.resizeObserver?.disconnect();
    this.resizeObserver = null;
    clearTimeout(this.resizeTimer);
    this.pendingResizePosition = null;
    this.lastStablePosition = null;
    cancelAnimationFrame(this.scrollFrame);
    for (const page of this.pages) page.renderTask?.cancel();
    this.pages = [];
    const loadingTask = this.loadingTask;
    const pdfDocument = this.pdfDocument;
    this.loadingTask = null;
    this.pdfDocument = null;
    this.pagesHost.replaceChildren();
    this.scroll.scrollTop = 0;
    this.host.classList.remove("is-loading", "has-error");
    this.setStatus("尚未載入 PDF");
    if (loadingTask) {
      try { await loadingTask.destroy(); } catch (error) { if (!cancelled(error)) console.warn("PDF loading cleanup failed", error); }
    }
    if (pdfDocument) {
      try { await pdfDocument.destroy(); } catch (error) { console.warn("PDF document cleanup failed", error); }
    }
  }

  async dispose() {
    await this.destroy();
    this.scroll.removeEventListener("scroll", this.onScroll);
    this.host.replaceChildren();
  }
}
