import type { IncomingMessage, ServerResponse } from "node:http";
import { getSignedDownloadUrl } from "../storage/s3";
import { prisma } from "../lib/prisma";
import { logger } from "../lib/logger";

/**
 * GET /documents/:id
 *
 * Returns a signed download URL for the document.
 * The URL is time-limited (default 15 minutes).
 */
export async function handleDownload(
  req: IncomingMessage,
  res: ServerResponse,
  documentId: string,
): Promise<void> {
  if (req.method !== "GET") {
    res.writeHead(405);
    res.end(JSON.stringify({ error: "Method not allowed" }));
    return;
  }

  try {
    const document = await prisma.document.findUnique({
      where: { id: documentId },
    });

    if (!document) {
      res.writeHead(404, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Document not found" }));
      return;
    }

    const signedUrl = await getSignedDownloadUrl(document.storageKey);

    logger.info({ docId: documentId }, "Signed URL generated");

    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        id: document.id,
        downloadUrl: signedUrl,
        contentType: document.contentType,
        sizeBytes: document.sizeBytes,
      }),
    );
  } catch (err) {
    logger.error({ err, documentId }, "Failed to generate download URL");
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Failed to generate download URL" }));
  }
}

/**
 * GET /documents/:id/metadata
 *
 * Returns document metadata without a download URL.
 */
export async function handleMetadata(
  req: IncomingMessage,
  res: ServerResponse,
  documentId: string,
): Promise<void> {
  if (req.method !== "GET") {
    res.writeHead(405);
    res.end(JSON.stringify({ error: "Method not allowed" }));
    return;
  }

  try {
    const document = await prisma.document.findUnique({
      where: { id: documentId },
    });

    if (!document) {
      res.writeHead(404, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Document not found" }));
      return;
    }

    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(document));
  } catch (err) {
    logger.error({ err, documentId }, "Failed to fetch document metadata");
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Failed to fetch metadata" }));
  }
}
