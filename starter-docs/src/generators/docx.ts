import { logger } from "../lib/logger";

export interface DocxOptions {
  templateId: string;
  data: Record<string, unknown>;
}

/**
 * Generate a DOCX document.
 *
 * TODO: Implement using the `docx` npm package or similar library.
 * This placeholder follows the same pattern as pdf.ts:
 * 1. Load template definition for the given templateId
 * 2. Substitute data into the document structure
 * 3. Return the DOCX file as a Buffer
 *
 * @returns DOCX file as a Buffer
 */
export async function generateDocx(options: DocxOptions): Promise<Buffer> {
  const { templateId, data } = options;

  logger.info({ templateId, dataKeys: Object.keys(data) }, "Generating DOCX");

  // {IMPLEMENT_DOCX_GENERATION}
  throw new Error(
    `DOCX generation not yet implemented (template: ${templateId})`,
  );
}
