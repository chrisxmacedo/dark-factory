import { NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  version: string;
  checks: {
    database: "ok" | "error";
    redis: "ok" | "error";
  };
}

export async function GET(): Promise<NextResponse<HealthStatus>> {
  const timestamp = new Date().toISOString();
  const version = process.env.OTEL_SERVICE_VERSION ?? "dev";

  let dbStatus: "ok" | "error" = "ok";
  let redisStatus: "ok" | "error" = "ok";

  // Check database
  try {
    await prisma.$queryRaw`SELECT 1`;
  } catch {
    dbStatus = "error";
  }

  // Check Redis
  try {
    await getRedis().ping();
  } catch {
    redisStatus = "error";
  }

  const allOk = dbStatus === "ok" && redisStatus === "ok";
  const status = allOk ? "healthy" : "degraded";

  return NextResponse.json(
    {
      status,
      timestamp,
      version,
      checks: {
        database: dbStatus,
        redis: redisStatus,
      },
    },
    { status: allOk ? 200 : 503 },
  );
}
