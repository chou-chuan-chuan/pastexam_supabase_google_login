import { PdfViewer } from "../assets/pdf-viewer.js";

function multiPagePdf(pageCount = 12) {
  const objects = [];
  const pageReferences = [];
  const fontObject = 3 + pageCount * 2;
  for (let index = 0; index < pageCount; index += 1) {
    const pageObject = 3 + index * 2;
    const contentObject = pageObject + 1;
    pageReferences.push(`${pageObject} 0 R`);
    const pageNumber = index + 1;
    const content = [
      "BT", "/F1 30 Tf", `72 700 Td (PDF Viewer QA - Page ${pageNumber} of ${pageCount}) Tj`,
      "/F1 16 Tf", `0 -55 Td (Scroll, jump, zoom, fit, rotate, and print this original PDF.) Tj`,
      `0 -40 Td (Page marker: ${String(pageNumber).padStart(2, "0")}) Tj`, "ET"
    ].join("\n");
    objects[pageObject] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 ${fontObject} 0 R >> >> /Contents ${contentObject} 0 R >>`;
    objects[contentObject] = `<< /Length ${content.length} >>\nstream\n${content}\nendstream`;
  }
  objects[1] = "<< /Type /Catalog /Pages 2 0 R >>";
  objects[2] = `<< /Type /Pages /Kids [${pageReferences.join(" ")}] /Count ${pageCount} >>`;
  objects[fontObject] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>";

  let pdf = "%PDF-1.4\n%QFW\n";
  const offsets = [0];
  for (let number = 1; number <= fontObject; number += 1) {
    offsets[number] = pdf.length;
    pdf += `${number} 0 obj\n${objects[number]}\nendobj\n`;
  }
  const xref = pdf.length;
  pdf += `xref\n0 ${fontObject + 1}\n0000000000 65535 f \n`;
  for (let number = 1; number <= fontObject; number += 1) {
    pdf += `${String(offsets[number]).padStart(10, "0")} 00000 n \n`;
  }
  pdf += `trailer\n<< /Size ${fontObject + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return new Blob([pdf], { type: "application/pdf" });
}

const viewer = new PdfViewer(document.querySelector("#fixtureViewer"), { label: "12 頁 PDF toolbar 測試" });
const pdfUrl = URL.createObjectURL(multiPagePdf());
window.fixturePdfViewer = viewer;
window.fixturePdfUrl = pdfUrl;
viewer.load(pdfUrl).catch(console.error);
window.addEventListener("beforeunload", () => {
  URL.revokeObjectURL(pdfUrl);
  void viewer.dispose();
});
