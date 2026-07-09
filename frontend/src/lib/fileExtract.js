import * as pdfjsLib from 'pdfjs-dist';
// Vite ?url import gives us a hosted URL for the worker script.
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.js?url';
import mammoth from 'mammoth';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

export async function extractTextFromFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  const buf = await file.arrayBuffer();

  if (ext === 'pdf') {
    const pdf = await pdfjsLib.getDocument({ data: buf }).promise;
    let text = '';
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map((it) => it.str).join(' ') + '\n';
    }
    return text.trim();
  }

  if (ext === 'docx') {
    const result = await mammoth.extractRawText({ arrayBuffer: buf });
    return result.value.trim();
  }

  if (ext === 'txt') {
    return new TextDecoder().decode(buf);
  }

  throw new Error(`Unsupported file type: .${ext} — upload a PDF, DOCX, or TXT file.`);
}
