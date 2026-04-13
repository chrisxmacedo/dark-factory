import Handlebars from "handlebars";
import fs from "node:fs";
import path from "node:path";
import { logger } from "./logger";

interface CompiledTemplate {
  subject: Handlebars.TemplateDelegate;
  html: Handlebars.TemplateDelegate;
  text: Handlebars.TemplateDelegate;
}

const templateCache = new Map<string, CompiledTemplate>();

const TEMPLATES_DIR =
  process.env.TEMPLATES_DIR ??
  path.join(__dirname, "..", "templates");

/**
 * Load and compile all templates from the templates directory.
 * Call once at startup.
 */
export function loadTemplates(): void {
  if (!fs.existsSync(TEMPLATES_DIR)) {
    logger.warn({ dir: TEMPLATES_DIR }, "Templates directory not found — skipping load");
    return;
  }

  const entries = fs.readdirSync(TEMPLATES_DIR, { withFileTypes: true });

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;

    const templateName = entry.name;
    const templateDir = path.join(TEMPLATES_DIR, templateName);

    try {
      const subjectPath = path.join(templateDir, "subject.hbs");
      const htmlPath = path.join(templateDir, "html.hbs");
      const textPath = path.join(templateDir, "text.hbs");

      // Subject and text are required; HTML is optional (falls back to text)
      if (!fs.existsSync(subjectPath) || !fs.existsSync(textPath)) {
        logger.warn({ templateName }, "Template missing subject.hbs or text.hbs — skipping");
        continue;
      }

      const subjectSrc = fs.readFileSync(subjectPath, "utf-8");
      const textSrc = fs.readFileSync(textPath, "utf-8");
      const htmlSrc = fs.existsSync(htmlPath)
        ? fs.readFileSync(htmlPath, "utf-8")
        : textSrc;

      templateCache.set(templateName, {
        subject: Handlebars.compile(subjectSrc),
        html: Handlebars.compile(htmlSrc),
        text: Handlebars.compile(textSrc),
      });

      logger.info({ templateName }, "Template loaded");
    } catch (err) {
      logger.error({ err, templateName }, "Failed to load template");
    }
  }

  logger.info({ count: templateCache.size }, "Templates loaded");
}

export interface RenderedNotification {
  subject: string;
  html: string;
  text: string;
}

/**
 * Render a notification template with the given data.
 */
export function renderTemplate(
  templateName: string,
  data: Record<string, unknown>,
): RenderedNotification {
  const compiled = templateCache.get(templateName);
  if (!compiled) {
    throw new Error(`Template not found: ${templateName}`);
  }

  return {
    subject: compiled.subject(data),
    html: compiled.html(data),
    text: compiled.text(data),
  };
}

/**
 * Check if a template exists in the cache.
 */
export function hasTemplate(templateName: string): boolean {
  return templateCache.has(templateName);
}
