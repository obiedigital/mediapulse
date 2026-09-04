import PDFDocument from "pdfkit";
import { aggregateSlide } from "./aggregate";
import type { SlideType } from "@/types/slides";

const INK = "#0A0A0F";
const ORANGE = "#FF5C1A";
const TEAL = "#00D4C8";
const MUTED = "#6B6B7A";

interface SlideForExport {
  id: string;
  order: number;
  type: string;
  config: unknown;
}

interface ResponseForExport {
  slideId: string;
  value: unknown;
  submittedAt: Date;
  participant: { id: string; demographicTags: unknown };
}

interface SessionForExport {
  id: string;
  title: string;
  type: string;
  status: string;
  createdAt: Date;
  participantCount: number;
}

export function buildSessionPdf(
  session: SessionForExport,
  slides: SlideForExport[],
  responses: ResponseForExport[]
): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margin: 48, size: "A4" });
    const chunks: Buffer[] = [];
    doc.on("data", (chunk) => chunks.push(chunk as Buffer));
    doc.on("end", () => resolve(Buffer.concat(chunks)));
    doc.on("error", reject);

    // --- Cover ---
    doc.rect(0, 0, doc.page.width, 120).fill(INK);
    doc
      .fillColor("#FFFFFF")
      .fontSize(22)
      .text("PulseCheck", 48, 36, { continued: false });
    doc
      .fillColor(TEAL)
      .fontSize(11)
      .text("Session results export", 48, 66);

    doc.moveDown(3);
    doc.fillColor(INK).fontSize(20).text(session.title, { align: "left" });
    doc
      .fillColor(MUTED)
      .fontSize(10)
      .text(
        `${session.type.replace("_", " ")} · ${session.status} · ${session.participantCount} participant(s) · created ${session.createdAt.toDateString()}`
      );
    doc.moveDown(1.5);

    for (const slide of slides) {
      const rows = responses
        .filter((r) => r.slideId === slide.id)
        .map((r) => ({ value: r.value, demographicTags: r.participant.demographicTags }));
      const result = aggregateSlide(slide.type as SlideType, slide.config, rows);

      doc.moveDown(1);
      doc.x = doc.page.margins.left;
      drawDivider(doc);
      doc.moveDown(0.5);
      doc.x = doc.page.margins.left;
      doc
        .fillColor(INK)
        .fontSize(14)
        .text(`Slide ${slide.order + 1} — ${labelForType(slide.type)}`, doc.page.margins.left, doc.y);
      const question =
        (slide.config as { question?: string; prompt?: string }).question ??
        (slide.config as { question?: string; prompt?: string }).prompt ??
        "";
      if (question) {
        doc.fillColor(MUTED).fontSize(10).text(question, doc.page.margins.left, doc.y, { width: 480 });
      }
      doc.moveDown(0.5);
      doc.x = doc.page.margins.left;

      if (result.type === "poll") {
        for (const opt of result.options) {
          drawBar(doc, opt.label, opt.count, opt.pct, result.totalResponses);
        }
        doc.moveDown(0.3);
        doc.x = doc.page.margins.left;
        doc.fillColor(MUTED).fontSize(9).text(`${result.totalResponses} response(s)`);
      } else if (result.type === "rating_scale") {
        doc.fillColor(INK).fontSize(11).text(`Average: ${result.average}`, doc.page.margins.left, doc.y);
        doc.moveDown(0.3);
        doc.x = doc.page.margins.left;
        const max = Math.max(1, ...result.distribution.map((d) => d.count));
        for (const d of result.distribution) {
          drawBar(doc, String(d.value), d.count, Math.round((d.count / max) * 100), null);
        }
        doc.moveDown(0.3);
        doc.x = doc.page.margins.left;
        doc.fillColor(MUTED).fontSize(9).text(`${result.totalResponses} response(s)`);
      } else if (result.type === "word_cloud") {
        doc.moveDown(0.2);
        const startX = doc.x;
        let x = startX;
        let y = doc.y;
        const maxCount = Math.max(1, ...result.words.map((w) => w.count));
        for (const w of result.words) {
          const size = 8 + Math.round((w.count / maxCount) * 16);
          doc.fontSize(size).fillColor(size > 16 ? ORANGE : INK);
          const width = doc.widthOfString(w.text + "  ");
          if (x + width > doc.page.width - doc.page.margins.right) {
            x = startX;
            y += size + 6;
          }
          doc.text(w.text + "  ", x, y, { continued: false, lineBreak: false });
          x += width;
        }
        doc.y = y + 24;
        doc.x = startX;
        doc.fillColor(MUTED).fontSize(9).text(`${result.totalResponses} response(s)`);
      } else if (result.type === "open_text") {
        doc.fillColor(MUTED).fontSize(9).text(`${result.totalResponses} response(s)`, doc.page.margins.left, doc.y);
        doc.moveDown(0.3);
        for (const text of result.responses.slice(0, 100)) {
          doc.x = doc.page.margins.left;
          doc.fillColor(INK).fontSize(9.5).text(`• ${text}`, { width: 480 });
        }
      }
    }

    // --- Raw response table (appendix) ---
    doc.addPage();
    doc.fillColor(INK).fontSize(16).text("Raw responses");
    doc.moveDown(0.5);
    doc.fillColor(MUTED).fontSize(8);
    for (const r of responses.slice(0, 500)) {
      const slide = slides.find((s) => s.id === r.slideId);
      const tags = (r.participant.demographicTags ?? {}) as Record<string, string>;
      const tagStr = Object.entries(tags)
        .map(([k, v]) => `${k}=${v}`)
        .join(", ");
      doc.text(
        `${r.submittedAt.toISOString()} · slide ${slide ? slide.order + 1 : "?"} (${slide?.type ?? "?"}) · ${tagStr || "no tags"} · ${JSON.stringify(r.value)}`
      );
    }

    doc.end();
  });
}

function labelForType(type: string) {
  switch (type) {
    case "poll":
      return "Poll";
    case "word_cloud":
      return "Word cloud";
    case "rating_scale":
      return "Rating scale";
    case "open_text":
      return "Open text";
    default:
      return type;
  }
}

function drawDivider(doc: PDFKit.PDFDocument) {
  const y = doc.y;
  doc
    .moveTo(doc.page.margins.left, y)
    .lineTo(doc.page.width - doc.page.margins.right, y)
    .strokeColor("#E5E5E5")
    .stroke();
}

function drawBar(
  doc: PDFKit.PDFDocument,
  label: string,
  count: number,
  pct: number,
  total: number | null
) {
  const barMaxWidth = 300;
  const x = doc.page.margins.left;
  const y = doc.y;
  doc.fillColor(INK).fontSize(9.5).text(label, x, y, { width: 140, continued: false });
  const barX = x + 150;
  const barWidth = Math.max(2, (pct / 100) * barMaxWidth);
  doc.rect(barX, y, barMaxWidth, 10).fillColor("#EDEDED").fill();
  doc.rect(barX, y, barWidth, 10).fillColor(ORANGE).fill();
  const suffix = total !== null ? `${count} (${pct}%)` : `${count}`;
  doc.fillColor(MUTED).fontSize(8.5).text(suffix, barX + barMaxWidth + 8, y);
  doc.y = y + 16;
  doc.x = x;
}
