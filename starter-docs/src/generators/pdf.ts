import puppeteer, { type Browser } from "puppeteer";
import { renderTemplate } from "../templates/manager";
import { logger } from "../lib/logger";

let browser: Browser | null = null;

/**
 * Get or launch the shared Puppeteer browser instance.
 */
export async function getBrowser(): Promise<Browser> {
  if (!browser || !browser.connected) {
    browser = await puppeteer.launch({
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
    });
    logger.info("Puppeteer browser launched");
  }
  return browser;
}

/**
 * Close the shared browser instance (for graceful shutdown).
 */
export async function closeBrowser(): Promise<void> {
  if (browser) {
    await browser.close();
    browser = null;
    logger.info("Puppeteer browser closed");
  }
}

export interface PdfOptions {
  templateId: string;
  data: Record<string, unknown>;
  format?: "A4" | "Letter";
  landscape?: boolean;
}

/**
 * Generate a PDF from a Handlebars template + data.
 *
 * 1. Render the template to HTML via Handlebars
 * 2. Load the HTML into a Puppeteer page
 * 3. Print to PDF
 *
 * @returns PDF file as a Buffer
 */
export async function generatePdf(options: PdfOptions): Promise<Buffer> {
  const { templateId, data, format = "A4", landscape = false } = options;

  logger.info({ templateId }, "Generating PDF");

  const html = renderTemplate(templateId, data);
  const instance = await getBrowser();
  const page = await instance.newPage();

  try {
    await page.setContent(html, { waitUntil: "networkidle0" });

    const pdfBuffer = await page.pdf({
      format,
      landscape,
      printBackground: true,
      margin: { top: "1cm", right: "1cm", bottom: "1cm", left: "1cm" },
    });

    logger.info(
      { templateId, sizeBytes: pdfBuffer.length },
      "PDF generated",
    );

    return Buffer.from(pdfBuffer);
  } finally {
    await page.close();
  }
}
