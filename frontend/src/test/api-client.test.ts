import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient, ApiException } from "@/lib/api-client";

describe("Typed API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("handles successful health check", async () => {
    const mockHealth = {
      status: "healthy",
      version: "0.1.0",
      environment: "test",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const result = await apiClient.getHealth();
    expect(result.status).toBe("healthy");
    expect(result.version).toBe("0.1.0");
  });

  it("propagates RFC 7807 error envelopes as ApiException", async () => {
    const errorPayload = {
      error: {
        code: "PAYLOAD_TOO_LARGE",
        message: "Word count exceeds limit.",
        details: [{ field: "text", issue: "Word count is 52000; limit is 50000" }],
        request_id: "req_test_123",
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 413,
      statusText: "Payload Too Large",
      json: async () => errorPayload,
    } as Response);

    await expect(apiClient.checkContent({ text: "long text..." })).rejects.toThrow(
      ApiException
    );

    try {
      await apiClient.checkContent({ text: "long text..." });
    } catch (err: unknown) {
      const apiErr = err as ApiException;
      expect(apiErr.status).toBe(413);
      expect(apiErr.code).toBe("PAYLOAD_TOO_LARGE");
      expect(apiErr.message).toBe("Word count exceeds limit.");
      expect(apiErr.requestId).toBe("req_test_123");
      expect(apiErr.details.length).toBe(1);
    }
  });
});
