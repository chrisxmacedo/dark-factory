import type { IncomingMessage, ServerResponse } from "node:http";
import { generatePdf } from "../generators/pdf";
import { generateDocx } from "../generators/docx";
import { uploadFile } from "../storage/s3";
import { prisma } from "../lib/prisma";
import { logger } from "../lib/logger";

interface GenerateRequest {
  templateId: string;
  format: "pdf" | "docx";
  data: Record<string, unknown>;
  ownerId: string;
  /** Optional logical key for versioning (e.g. "invoice-2026-03") */
  logicalKey?: string;
}

/**
 * POST /generate
 *
 * Accepts a template ID, format, owner, and data payload.
 * Generates the document, uploads to S3, saves metadata, returns the record.
 */
export async function handleGenerate(
  req: IncomingMessage,
  res: ServerResponse,
): Promise<void> {
  if (req.method !== "POST") {
    res.writeHead(405);
    res.end(JSON.stringify({ error: "Method not allowed" }));
    return;
  }

  let body: GenerateRequest;
  try {
    const chunks: Buffer[] = [];
    for await (const chunk of req) {
      chunks.push(chunk as Buffer);
    }
    body = JSON.parse(Buffer.concat(chunks).toString("utf-8")) as GenerateRequest;
  } catch {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Invalid JSON body" }));
    return;
  }

  const { templateId, format, data, ownerId, logicalKey } = body;

  if (!templateId || !format || !data || !ownerId) {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        error: "Missing required fields: templateId, format, data, ownerId",
      }),
    );
    return;
  }

  try {
    // Determine version number
    let version = 1;
    if (logicalKey) {
      // {QUERY_EXISTING_VERSIONS_BY_LOGICAL_KEY}
      const existing = await prisma.document.count({
        where: { ownerId, templateId, logicalKey },
      });
      version = existing + 1;
    }

    // Generate document
    let buffer: Buffer;
    let contentType: string;

    if (format === "pdf") {
      buffer = await generatePdf({ templateId, data });
      contentType = "application/pdf";
    } else if (format === "docx") {
      buffer = await generateDocx({ templateId, data });
      contentType =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
    } else {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: `Unsupported format: ${format}` }));
      return;
    }

    // Upload to S3
    const storageKey = `${ownerId}/${templateId}/${logicalKey ?? "default"}/v${version}.${format}`;
    await uploadFile(storageKey, buffer, contentType);

    // Save metadata
    const document = await prisma.document.create({
      data: {
        type: format,
        ownerId,
        templateId,
        logicalKey: logicalKey ?? null,
        storageKey,
        version,
        contentType,
        sizeBytes: buffer.length,
      },
    });

    logger.info(
      { docId: document.id, templateId, format, version },
      "Document generated and stored",
    );

    res.writeHead(201, { "Content-Type": "application/json" });
    res.end(JSON.stringify(document));
  } catch (err) {
    logger.error({ err, templateId, format }, "Document generation failed");
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Document generation failed" }));
  }
}
