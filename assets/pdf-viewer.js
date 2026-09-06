import {
  clampPageNumber,
  clampedRenderPixelRatio,
  clampZoom,
  normalizeRotation,
  rotatedPageDimensions,
  scaleForViewMode,
  stepZoom,
  zoomPercentage
} from "./pdf-viewer-utils.js";

export const PDFJS_VERSION = "4.10.38";
export const PDFJS_MODULE_URL = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${PDFJS_VERSION}/build/pdf.min.mjs`;
export const PDFJS_WORKER_URL = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${PDFJS_VERSION}/build/pdf.worker.min.mjs`;

let pdfJsPromise;
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.1;
const DEFAULT_VIEW_MODE = "fit-width";

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

function toolButton(text, label) {
  const button = element("button", "pdf-viewer-tool-button", text);
  button.type = "button";
  button.title = label;
  button.setAttribute("aria-label", label);
  button.disabled = true;
  return button;
}

export class PdfViewer {
  constructor(host, { label = "PDF 文件閱讀器" } = {}) {
    if (!(host instanceof HTMLElement)) throw new TypeError("PdfViewer 需要有效的容器。");
    this.host = host;
    this.host.classList.add("pdf-viewer");
    this.toolbar = element("div", "pdf-viewer-toolbar");
    this.toolbar.setAttribute("role", "toolbar");
    this.toolbar.setAttribute("aria-label", "PDF 文件控制");
    this.pageGroup = element("div", "pdf-viewer-toolbar-group pdf-viewer-page-group");
    this.pageInput = element("input", "pdf-viewer-page-input");
    this.pageInput.type = "number";
    this.pageInput.inputMode = "numeric";
    this.pageInput.min = "1";
    this.pageInput.value = "1";
    this.pageInput.disabled = true;
    this.pageInput.setAttribute("aria-label", "PDF 頁碼");
    this.totalPages = element("span", "pdf-viewer-page-total", "/ 0");
    this.pageGroup.append(this.pageInput, this.totalPages);

    this.zoomGroup = element("div", "pdf-viewer-toolbar-group");
    this.zoomOutButton = toolButton("−", "縮小 PDF");
    this.zoomLabel = element("span", "pdf-viewer-zoom-label", "100%");
    this.zoomLabel.setAttribute("aria-live", "polite");
    this.zoomInButton = toolButton("+", "放大 PDF");
    this.zoomGroup.append(this.zoomOutButton, this.zoomLabel, this.zoomInButton);

    this.fitGroup = element("div", "pdf-viewer-toolbar-group");
    this.fitPageButton = toolButton("整頁", "符合整頁");
    this.fitWidthButton = toolButton("頁寬", "符合頁寬");
    this.fitGroup.append(this.fitPageButton, this.fitWidthButton);

    this.rotateGroup = element("div", "pdf-viewer-toolbar-group");
    this.rotateLeftButton = toolButton("↶", "向左旋轉");
    this.rotateRightButton = toolButton("↷", "向右旋轉");
    this.rotateGroup.append(this.rotateLeftButton, this.rotateRightButton);

    this.documentGroup = element("div", "pdf-viewer-toolbar-group");
    this.printButton = toolButton("列印", "列印 PDF");
    this.documentGroup.append(this.printButton);
    this.toolbar.append(this.pageGroup, this.zoomGroup, this.fitGroup, this.rotateGroup, this.documentGroup);

    this.status = element("div", "pdf-viewer-status", "尚未載入 PDF");
    this.status.setAttribute("role", "status");
    this.status.setAttribute("aria-live", "polite");
    this.scroll = element("div", "pdf-viewer-scroll");
    this.scroll.tabIndex = 0;
    this.scroll.setAttribute("role", "document");
    this.scroll.setAttribute("aria-label", label);
    this.pagesHost = element("div", "pdf-viewer-pages");
    this.scroll.append(this.pagesHost);
    this.host.replaceChildren(this.toolbar, this.status, this.scroll);

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
    this.viewMode = DEFAULT_VIEW_MODE;
    this.customZoom = 1;
    this.rotation = 0;
    this.currentPage = 1;
    this.pdfBytes = null;
    this.printBlobUrl = null;
    this.printFrame = null;
    this.printCleanupTimer = 0;
    this.toolbarAbortController = new AbortController();
    this.onScroll = () => {
      this.lastStablePosition = this.capturePosition();
      this.schedulePageStatusUpdate();
    };
    this.scroll.addEventListener("scroll", this.onScroll, { passive: true });
    this.bindToolbar();
    this.updateToolbarState();
  }

  setStatus(text, kind = "") {
    this.status.textContent = text;
    this.status.className = `pdf-viewer-status${kind ? ` is-${kind}` : ""}`;
  }

  bindToolbar() {
    const options = { signal: this.toolbarAbortController.signal };
    const commitPage = () => this.goToPage(this.pageInput.value);
    this.pageInput.addEventListener("change", commitPage, options);
    this.pageInput.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      commitPage();
    }, options);
    this.zoomOutButton.addEventListener("click", () => this.zoomBy(-1), options);
    this.zoomInButton.addEventListener("click", () => this.zoomBy(1), options);
    this.fitPageButton.addEventListener("click", () => this.setViewMode("fit-page"), options);
    this.fitWidthButton.addEventListener("click", () => this.setViewMode("fit-width"), options);
    this.rotateLeftButton.addEventListener("click", () => this.rotateBy(-90), options);
    this.rotateRightButton.addEventListener("click", () => this.rotateBy(90), options);
    this.printButton.addEventListener("click", () => this.printOriginalPdf(), options);
    this.host.addEventListener("keydown", (event) => {
      if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
      if (event.key === "+" || event.key === "=") {
        event.preventDefault();
        this.zoomBy(1);
      } else if (event.key === "-") {
        event.preventDefault();
        this.zoomBy(-1);
      } else if (event.key === "0") {
        event.preventDefault();
        this.setViewMode("fit-page");
      }
    }, options);
  }

  controls() {
    return [
      this.zoomOutButton, this.zoomInButton, this.fitPageButton, this.fitWidthButton,
      this.rotateLeftButton, this.rotateRightButton, this.printButton
    ];
  }

  currentPageState() {
    return this.pages[clampPageNumber(this.currentPage, this.pages.length) - 1] || this.pages[0] || null;
  }

  currentScale() {
    return this.currentPageState()?.scale || (this.viewMode === "custom" ? this.customZoom : 0);
  }

  updateToolbarState() {
    const loaded = Boolean(this.pdfDocument && this.pages.length);
    this.pageInput.disabled = !loaded;
    this.pageInput.max = String(this.pages.length || 1);
    this.pageInput.value = String(loaded ? clampPageNumber(this.currentPage, this.pages.length) : 1);
    this.totalPages.textContent = `/ ${this.pages.length}`;
    this.zoomLabel.textContent = `${zoomPercentage(this.currentScale()) || 100}%`;
    for (const control of this.controls()) control.disabled = !loaded;
    if (loaded) {
      this.zoomOutButton.disabled = this.viewMode === "custom" && this.customZoom <= MIN_ZOOM;
      this.zoomInButton.disabled = this.viewMode === "custom" && this.customZoom >= MAX_ZOOM;
    }
    this.fitPageButton.setAttribute("aria-pressed", String(this.viewMode === "fit-page"));
    this.fitWidthButton.setAttribute("aria-pressed", String(this.viewMode === "fit-width"));
    this.rotateLeftButton.dataset.rotation = String(this.rotation);
    this.rotateRightButton.dataset.rotation = String(this.rotation);
  }

  goToPage(pageNumber) {
    if (!this.pages.length) return false;
    const number = clampPageNumber(pageNumber, this.pages.length);
    const page = this.pages[number - 1];
    this.currentPage = number;
    this.pageInput.value = String(number);
    this.scroll.scrollTo({
      top: Math.max(0, this.pageScrollOffset(page) + page.height / 2 - this.scroll.clientHeight / 2),
      behavior: "auto"
    });
    this.lastStablePosition = this.capturePosition();
    this.updatePageStatus();
    this.renderNearbyPages(this.generation);
    return true;
  }

  applyViewChange(position = this.capturePosition()) {
    if (!this.pages.length) return;
    for (const page of this.pages) page.renderTask?.cancel();
    this.layoutPages(false, position);
    this.lastStablePosition = this.capturePosition();
    this.renderNearbyPages(this.generation);
    this.updatePageStatus();
  }

  setViewMode(mode) {
    if (!["fit-page", "fit-width"].includes(mode) || !this.pages.length) return false;
    const position = this.capturePosition();
    this.viewMode = mode;
    this.applyViewChange(position);
    return true;
  }

  zoomBy(direction) {
    if (!this.pages.length) return false;
    const position = this.capturePosition();
    const startingScale = this.currentScale() || 1;
    this.customZoom = stepZoom(startingScale, direction, ZOOM_STEP, MIN_ZOOM, MAX_ZOOM);
    this.viewMode = "custom";
    this.applyViewChange(position);
    return true;
  }

  rotateBy(delta) {
    if (!this.pages.length) return false;
    const position = this.capturePosition();
    this.rotation = normalizeRotation(this.rotation + delta);
    this.applyViewChange(position);
    return true;
  }

  clearPrintResources() {
    clearTimeout(this.printCleanupTimer);
    this.printCleanupTimer = 0;
    this.printFrame?.remove();
    this.printFrame = null;
    if (this.printBlobUrl) URL.revokeObjectURL(this.printBlobUrl);
    this.printBlobUrl = null;
  }

  printOriginalPdf() {
    if (!this.pdfBytes?.byteLength) return false;
    this.clearPrintResources();
    this.printBlobUrl = URL.createObjectURL(new Blob([this.pdfBytes.slice()], { type: "application/pdf" }));
    const frame = element("iframe", "pdf-viewer-print-frame");
    frame.title = "PDF 列印文件";
    frame.setAttribute("aria-hidden", "true");
    frame.tabIndex = -1;
    frame.addEventListener("load", () => {
      try {
        frame.contentWindow?.focus();
        frame.contentWindow?.print();
      } catch (error) {
        console.warn("PDF inline print unavailable; opening the original PDF instead.", error);
        window.open(this.printBlobUrl, "_blank", "noopener,noreferrer");
      }
    }, { once: true });
    frame.src = this.printBlobUrl;
    document.body.append(frame);
    this.printFrame = frame;
    // Browser PDF plugins may keep reading the Blob while the print dialog is
    // open. Delayed cleanup avoids invalidating the original document early.
    this.printCleanupTimer = setTimeout(() => this.clearPrintResources(), 60_000);
    return true;
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
    this.viewMode = DEFAULT_VIEW_MODE;
    this.customZoom = 1;
    this.rotation = 0;
    this.currentPage = 1;
    this.updateToolbarState();
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
      this.pdfBytes = bytes.slice();

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
      this.currentPage = 1;
      this.setStatus(`1 / ${pdfDocument.numPages}`);
      this.updateToolbarState();
      await this.renderPage(this.pages[0], generation);
      return true;
    } catch (error) {
      if (generation !== this.generation || cancelled(error)) return false;
      this.pdfBytes = null;
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
        rotation: 0,
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
      xRatio: this.scroll.scrollLeft / Math.max(1, this.scroll.scrollWidth - this.scroll.clientWidth),
      atStart: scrollTop < 2,
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
      const rotated = rotatedPageDimensions(page.baseViewport.width, page.baseViewport.height, this.rotation);
      const scale = scaleForViewMode(
        this.viewMode, available.width, available.height,
        rotated.width, rotated.height, this.customZoom
      );
      const width = rotated.width * scale;
      const height = rotated.height * scale;
      const changed = Math.abs(page.width - width) > 0.5 || Math.abs(page.height - height) > 0.5 || page.rotation !== this.rotation;
      page.scale = scale;
      page.rotation = this.rotation;
      page.width = width;
      page.height = height;
      page.element.style.width = `${width}px`;
      page.element.style.height = `${height}px`;
      if (changed && (page.rendered || page.renderTask)) this.resetRenderedPage(page);
    }

    if (position) {
      const anchor = this.pages[position.number - 1];
      this.scroll.scrollTop = position.atStart
        ? 0
        : position.atEnd
          ? this.scroll.scrollHeight
          : Math.max(0, this.pageScrollOffset(anchor) + position.ratio * anchor.height - this.scroll.clientHeight / 2);
      this.scroll.scrollLeft = Math.max(
        0,
        (position.xRatio || 0) * Math.max(0, this.scroll.scrollWidth - this.scroll.clientWidth)
      );
    }
    this.updateToolbarState();
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
    const viewport = page.page.getViewport({
      scale: page.scale,
      rotation: normalizeRotation((page.page.rotate || 0) + this.rotation)
    });
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
    const maxScrollTop = Math.max(0, this.scroll.scrollHeight - this.scroll.clientHeight);
    if (this.scroll.scrollTop <= 1) {
      this.currentPage = 1;
      this.setStatus(`1 / ${this.pages.length}`);
      this.updateToolbarState();
      return;
    }
    if (maxScrollTop > 0 && this.scroll.scrollTop >= maxScrollTop - 1) {
      this.currentPage = this.pages.length;
      this.setStatus(`${this.pages.length} / ${this.pages.length}`);
      this.updateToolbarState();
      return;
    }
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
    this.currentPage = current.number;
    this.setStatus(`${current.number} / ${this.pages.length}`);
    this.updateToolbarState();
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
    this.clearPrintResources();
    this.pages = [];
    const loadingTask = this.loadingTask;
    const pdfDocument = this.pdfDocument;
    this.loadingTask = null;
    this.pdfDocument = null;
    this.pdfBytes = null;
    this.pagesHost.replaceChildren();
    this.scroll.scrollTop = 0;
    this.scroll.scrollLeft = 0;
    this.viewMode = DEFAULT_VIEW_MODE;
    this.customZoom = 1;
    this.rotation = 0;
    this.currentPage = 1;
    this.host.classList.remove("is-loading", "has-error");
    this.setStatus("尚未載入 PDF");
    this.updateToolbarState();
    if (loadingTask) {
      try { await loadingTask.destroy(); } catch (error) { if (!cancelled(error)) console.warn("PDF loading cleanup failed", error); }
    }
    if (pdfDocument) {
      try { await pdfDocument.destroy(); } catch (error) { console.warn("PDF document cleanup failed", error); }
    }
  }

  async dispose() {
    await this.destroy();
    this.toolbarAbortController.abort();
    this.scroll.removeEventListener("scroll", this.onScroll);
    this.host.replaceChildren();
  }
}
