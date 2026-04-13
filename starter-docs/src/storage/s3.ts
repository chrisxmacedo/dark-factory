import {
  S3Client,
  PutObjectCommand,
  GetObjectCommand,
  HeadBucketCommand,
  type PutObjectCommandInput,
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { logger } from "../lib/logger";

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

function getBucket(): string {
  const bucket = process.env.S3_BUCKET;
  if (!bucket) {
    throw new Error("S3_BUCKET environment variable is not set");
  }
  return bucket;
}

/**
 * Upload a buffer to S3/MinIO.
 */
export async function uploadFile(
  key: string,
  body: Buffer,
  contentType: string,
): Promise<string> {
  const params: PutObjectCommandInput = {
    Bucket: getBucket(),
    Key: key,
    Body: body,
    ContentType: contentType,
  };

  const s3 = getClient();
  await s3.send(new PutObjectCommand(params));
  logger.info({ key, contentType }, "File uploaded to S3");

  return key;
}

/**
 * Download a file from S3/MinIO as a Buffer.
 */
export async function downloadFile(key: string): Promise<Buffer> {
  const s3 = getClient();
  const response = await s3.send(
    new GetObjectCommand({
      Bucket: getBucket(),
      Key: key,
    }),
  );

  const stream = response.Body;
  if (!stream) {
    throw new Error(`Empty response body for key: ${key}`);
  }

  // Collect stream into buffer
  const chunks: Uint8Array[] = [];
  for await (const chunk of stream as AsyncIterable<Uint8Array>) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

/**
 * Generate a time-limited signed URL for downloading a file.
 */
export async function getSignedDownloadUrl(
  key: string,
  expiresInSeconds?: number,
): Promise<string> {
  const expiry = expiresInSeconds ??
    parseInt(process.env.SIGNED_URL_EXPIRY_SECONDS ?? "900", 10);

  const s3 = getClient();
  const command = new GetObjectCommand({
    Bucket: getBucket(),
    Key: key,
  });

  return getSignedUrl(s3, command, { expiresIn: expiry });
}

/**
 * Check S3/MinIO connectivity by issuing a HeadBucket request.
 */
export async function checkS3Connectivity(): Promise<boolean> {
  try {
    const s3 = getClient();
    await s3.send(new HeadBucketCommand({ Bucket: getBucket() }));
    return true;
  } catch {
    return false;
  }
}
