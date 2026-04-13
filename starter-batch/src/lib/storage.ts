import {
  S3Client,
  PutObjectCommand,
  type PutObjectCommandInput,
} from "@aws-sdk/client-s3";

let client: S3Client | null = null;

function getClient(): S3Client {
  if (!client) {
    client = new S3Client({
      endpoint: process.env.S3_ENDPOINT,
      region: process.env.S3_REGION || "us-east-1",
      credentials: {
        accessKeyId: process.env.S3_ACCESS_KEY || "",
        secretAccessKey: process.env.S3_SECRET_KEY || "",
      },
      forcePathStyle: true, // Required for MinIO
    });
  }
  return client;
}

/**
 * Upload a buffer or string to S3/MinIO.
 *
 * @param key    - Object key (e.g. "reports/2026-03-31/reconciliation.csv")
 * @param body   - File content as Buffer or string
 * @param contentType - MIME type (e.g. "text/csv", "application/json")
 * @returns The full S3 key of the uploaded object
 */
export async function uploadFile(
  key: string,
  body: Buffer | string,
  contentType: string
): Promise<string> {
  const bucket = process.env.S3_BUCKET;
  if (!bucket) {
    throw new Error("S3_BUCKET environment variable is not set");
  }

  const params: PutObjectCommandInput = {
    Bucket: bucket,
    Key: key,
    Body: typeof body === "string" ? Buffer.from(body, "utf-8") : body,
    ContentType: contentType,
  };

  const s3 = getClient();
  await s3.send(new PutObjectCommand(params));

  return key;
}
