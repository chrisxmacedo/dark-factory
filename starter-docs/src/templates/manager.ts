import fs from "node:fs";
import path from "node:path";
import Handlebars from "handlebars";
import { logger } from "../lib/logger";

const templateCache = new Map<string, HandlebarsTemplateDelegate>();

const TEMPLATES_DIR =
  process.env.TEMPLATES_DIR ?? path.join(__dirname, "../../templates");

/**
 * Load and compile a Handlebars template by name.
 * Templates are cached after first load.
 *
 * @param templateId - Template filename without extension (e.g. "invoice")
 * @returns Compiled Handlebars template function
 */
export function getTemplate(templateId: string): HandlebarsTemplateDelegate {
  const cached = templateCache.get(templateId);
  if (cached) {
    return cached;
  }

  const filePath = path.join(TEMPLATES_DIR, `${templateId}.hbs`);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Template not found: ${templateId} (looked at ${filePath})`);
  }

  const source = fs.readFileSync(filePath, "utf-8");
  const compiled = Handlebars.compile(source);
  templateCache.set(templateId, compiled);

  logger.info({ templateId, filePath }, "Template compiled and cached");
  return compiled;
}

/**
 * Render a template with the given data.
 *
 * @param templateId - Template identifier
 * @param data - Variables to substitute into the template
 * @returns Rendered HTML string
 */
export function renderTemplate(
  templateId: string,
  data: Record<string, unknown>,
): string {
  const template = getTemplate(templateId);
  return template(data);
}

/**
 * Clear the template cache (useful for development/testing).
 */
export function clearTemplateCache(): void {
  templateCache.clear();
  logger.info("Template cache cleared");
}
