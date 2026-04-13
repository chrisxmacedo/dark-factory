import { createCipheriv, createDecipheriv, createHash, randomBytes } from "crypto";

const ALGORITHM = "aes-256-gcm";
const IV_LENGTH = 16;
const TAG_LENGTH = 16;

let cachedKey: Buffer | null = null;

function getEncryptionKey(): Buffer {
  if (cachedKey) return cachedKey;

  const secret = process.env.ENCRYPTION_KEY ?? process.env.NEXTAUTH_SECRET;
  if (!secret) {
    throw new Error(
      "ENCRYPTION_KEY or NEXTAUTH_SECRET is required for encryption",
    );
  }
  // Derive a 32-byte key from the secret using SHA-256
  cachedKey = createHash("sha256").update(secret).digest();
  return cachedKey;
}

/**
 * Encrypt a string value using AES-256-GCM.
 * Returns a base64-encoded string containing IV + ciphertext + auth tag.
 */
export function encrypt(plaintext: string): string {
  const key = getEncryptionKey();
  const iv = randomBytes(IV_LENGTH);
  const cipher = createCipheriv(ALGORITHM, key, iv);

  let encrypted = cipher.update(plaintext, "utf8", "hex");
  encrypted += cipher.final("hex");
  const tag = cipher.getAuthTag();

  // Concatenate: IV (16) + tag (16) + ciphertext
  const combined = Buffer.concat([iv, tag, Buffer.from(encrypted, "hex")]);

  return combined.toString("base64");
}

/**
 * Decrypt a base64-encoded string that was encrypted with encrypt().
 */
export function decrypt(encryptedBase64: string): string {
  const key = getEncryptionKey();
  const combined = Buffer.from(encryptedBase64, "base64");

  const iv = combined.subarray(0, IV_LENGTH);
  const tag = combined.subarray(IV_LENGTH, IV_LENGTH + TAG_LENGTH);
  const ciphertext = combined.subarray(IV_LENGTH + TAG_LENGTH);

  const decipher = createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(tag);

  let decrypted = decipher.update(ciphertext);
  decrypted = Buffer.concat([decrypted, decipher.final()]);

  return decrypted.toString("utf8");
}
