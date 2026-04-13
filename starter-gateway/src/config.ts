function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

function optionalEnv(key: string, fallback: string): string {
  return process.env[key] ?? fallback;
}

export const config = {
  port: parseInt(optionalEnv("PORT", "3000"), 10),
  nodeEnv: optionalEnv("NODE_ENV", "development"),
  logLevel: optionalEnv("LOG_LEVEL", "info"),

  // Auth
  jwtIssuer: requireEnv("JWT_ISSUER"),
  jwtAudience: requireEnv("JWT_AUDIENCE"),
  jwksUri: requireEnv("JWKS_URI"),

  // Redis
  redisUrl: requireEnv("REDIS_URL"),

  // Rate limiting
  rateLimitWindowMs: parseInt(optionalEnv("RATE_LIMIT_WINDOW_MS", "60000"), 10),
  rateLimitMaxAuthenticated: parseInt(
    optionalEnv("RATE_LIMIT_MAX_AUTHENTICATED", "100"),
    10
  ),
  rateLimitMaxAnonymous: parseInt(
    optionalEnv("RATE_LIMIT_MAX_ANONYMOUS", "20"),
    10
  ),

  // Internal services — add entries per downstream service
  // {SERVICE_NAME}_URL: requireEnv("{SERVICE_NAME}_URL"),

  // CORS
  corsOrigins: optionalEnv("CORS_ORIGINS", "http://localhost:3001").split(","),

  // OpenTelemetry
  otelEndpoint: optionalEnv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
  otelServiceName: optionalEnv("OTEL_SERVICE_NAME", "{PROJECT_NAME}-gateway"),
} as const;
