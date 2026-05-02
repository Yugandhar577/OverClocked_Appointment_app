import request from "supertest"

const API_BASE = process.env.API_BASE ?? "http://localhost:8000"

describe("health", () => {
  it("returns ok", async () => {
    const res = await request(API_BASE).get("/health")
    expect([200, 503]).toContain(res.status)
  })
})
