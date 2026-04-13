import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { v4 as uuidv4 } from "uuid";

const HEADER_REQUEST_ID = "x-request-id";

/**
 * Next.js middleware: adds correlation ID (X-Request-Id) to all requests.
 * If the incoming request already has the header, it is preserved.
 * Otherwise a new UUID v4 is generated.
 */
export function middleware(request: NextRequest) {
  const requestId = request.headers.get(HEADER_REQUEST_ID) ?? uuidv4();

  // Clone the request headers and set the correlation ID
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set(HEADER_REQUEST_ID, requestId);

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  });

  // Propagate to response headers
  response.headers.set(HEADER_REQUEST_ID, requestId);

  return response;
}

export const config = {
  matcher: [
    // Match all API routes and pages, exclude static files and Next.js internals
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
